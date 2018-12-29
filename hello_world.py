# -*- coding: utf-8 -*-
#https://i.ibb.co/rkk11QZ/shoot.png
#https://i.ibb.co/V3QNWkB/sheild.png
#https://i.ibb.co/Z1qZnKW/reload.png
# This is a simple Hello World Alexa Skill, built using
# the implementation of handler classes approach in skill builder.
from __future__ import print_function
import logging
import random
import boto3
import json
from boto3.dynamodb.conditions import Key, Attr

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand,
    AutoPageCommand, HighlightMode)

dynamodb = boto3.resource('dynamodb')
Table = dynamodb.Table('shootoutTable')
sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
def formatAPL(action, ammo):
    with open('preLayout.json') as fin, open('/tmp/layout.json', 'w') as fout:
        for i, item in enumerate(fin, 1):
            if i == 32: 
                item = ' "headerTitle": "Ammo: ' +str(ammo)+' " \n'
            elif i==47:
                if(action=="Reload"):
                    item = '"source": "https://i.ibb.co/Z1qZnKW/reload.png",'
                elif(action=="Shoot"):
                    item = '"source": "https://i.ibb.co/rkk11QZ/shoot.png",'
                else:
                    item = '"source": "https://i.ibb.co/V3QNWkB/sheild.png",'
            fout.write(item)
def _load_apl_document(file_path):
    # type: (str) -> Dict[str, Any]
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)

def decideAction():
    entity = Table.get_item(Key={'name': 'game'})
    alexaBullets = entity['Item']['alexaBullets']
    userBullets = entity['Item']['userBullets']
    answer = "Sheild"
    if (alexaBullets==0):
        if(userBullets==0):
            answer =  "Reload"
        else:
            num = random.random()
            if(num < 0.33):
                answer =  "Reload"
            else:
                answer =  "Sheild"
    elif (userBullets==0):
        num = random.randint(0,1)
        if(num):
            answer =  "Shoot"
        else:
            answer = "Reload"
    else:
        ratio = min(userBullets,alexaBullets) / max(userBullets,alexaBullets)
        num = random.random()
        if(userBullets == alexaBullets):
            shootThresh = 0.35
        elif(userBullets > alexaBullets):
            shootThresh = ratio
        else:
            shootThresh = 1 -ratio
        reloadThresh = float(shootThresh) + (1-float(shootThresh))/4
        print("ShootThresh: "+str(shootThresh)),
        print(" ReloadThresh: "+str(reloadThresh)),
        print(" "+str(num))
        if(num < shootThresh):
            answer = "Shoot"
        elif (num < reloadThresh):
            answer = "Reload"
        else:
            answer = "Sheild"
            
    if (answer == "Reload"):
        alexaBullets= alexaBullets+1
        response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set alexaBullets = :m",
            ExpressionAttributeValues={
                ':m': alexaBullets
            },
            ReturnValues="UPDATED_NEW"
        )
    elif (answer == "Shoot"):
        alexaBullets = alexaBullets -1
        response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set alexaBullets = :m",
            ExpressionAttributeValues={
                ':m': alexaBullets
            },
            ReturnValues="UPDATED_NEW"
        )
    return answer

def newRound(alexaWon):
    entity = Table.get_item(Key={'name': 'game'})
    alexaScore = entity['Item']['alexaScore']
    userScore = entity['Item']['userScore']
    if(alexaWon):
        alexaScore = alexaScore+1
        response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set alexaScore = :m",
            ExpressionAttributeValues={
                ':m': alexaScore
            },
            ReturnValues="UPDATED_NEW"
        )
        scoreRead = " Got'em."
    else:
        userScore = userScore+1
        response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set userScore = :m",
            ExpressionAttributeValues={
                ':m': userScore
            },
            ReturnValues="UPDATED_NEW"
        )
        scoreRead = " Ouch."
       
    print("Resetting Bullets") 
    response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set alexaBullets = :z, userBullets = :z",
            ExpressionAttributeValues={
                ':z': 0
            },
            ReturnValues="UPDATED_NEW"
        )
    response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set userBullets = :z",
            ExpressionAttributeValues={
                ':z': 0
            },
            ReturnValues="UPDATED_NEW"
        )
    scoreRead = scoreRead+" I have "+str(alexaScore)+" points and you have "+str(userScore)+" points"
    return scoreRead
    
def resolveAction(userAction, alexaAction):
    answer = "I chose to "+alexaAction+"."
    if(userAction=="Shoot" and alexaAction=="Shoot"):
        answer = "We both missed"
    elif(userAction=="Shoot" and alexaAction=="Reload"):
        answer = answer + newRound(0)
    elif(userAction=="Reload" and alexaAction=="Shoot"):
        answer  = answer + newRound(1)
    return answer
    
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        response = Table.update_item(
            Key={
                'name': 'game'
             },
            UpdateExpression="set alexaBullets = :z, userBullets = :z, alexaScore = :z, userScore = :z",
            ExpressionAttributeValues={
                ':z': 0
            },
            ReturnValues="UPDATED_NEW"
        )
        speech_text = "Welcome to shootout. Ask for Help if you don't know how to play. There's only space for one sherrif in this town, so draw your Guns!"
        
        formatAPL("Sheild",0)
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False).add_directive(
                RenderDocumentDirective(
                    document=_load_apl_document("/tmp/layout.json")
                )
            )
        return handler_input.response_builder.response

class ReloadIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("ReloadIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        entity = Table.get_item( Key={ 'name': 'game' })
        origAlexaScore = entity['Item']['alexaScore']
        origUserScore = entity['Item']['userScore']
        action = decideAction()
        speech_text = resolveAction("Reload",action)
        entity = Table.get_item( Key={ 'name': 'game' })
        formatAPL(action,0)
        if(origAlexaScore==entity['Item']['alexaScore'] and origUserScore==entity['Item']['userScore']):
            userBullets = entity['Item']['userBullets']
            response = Table.update_item(
                Key={
                    'name': 'game'
                },
                UpdateExpression="set userBullets = :m",
                ExpressionAttributeValues={
                    ':m': userBullets+1
                },
                ReturnValues="UPDATED_NEW"
            )
            formatAPL(action,userBullets+1)
        
        
        
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False).add_directive(
                RenderDocumentDirective(
                    document=_load_apl_document("/tmp/layout.json")
                )
            )
            
        return handler_input.response_builder.response
        
class SheildIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("SheildIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        action = decideAction()
        speech_text = resolveAction("Sheild",action)
        entity = Table.get_item( Key={ 'name': 'game' })
        ammo = entity['Item']['userBullets']
        formatAPL(action,ammo)
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False).add_directive(
                RenderDocumentDirective(
                    document=_load_apl_document("/tmp/layout.json")
                )
            )
            
        return handler_input.response_builder.response

class ShootIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("ShootIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        entity = Table.get_item( Key={ 'name': 'game' })
        userBullets = entity['Item']['userBullets']
        entity = Table.get_item( Key={ 'name': 'game' })
        origAlexaScore = entity['Item']['alexaScore']
        origUserScore = entity['Item']['userScore']
        if (userBullets < 1):
            speech_text = "You are shooting blanks partner"
        else:
            action = decideAction()
            speech_text = resolveAction("Shoot",action)
            entity = Table.get_item( Key={ 'name': 'game' })
            if(origAlexaScore==entity['Item']['alexaScore'] and origUserScore==entity['Item']['userScore']):
                response = Table.update_item(
                    Key={
                        'name': 'game'
                    },
                    UpdateExpression="set userBullets = :m",
                    ExpressionAttributeValues={
                        ':m': userBullets-1
                    },
                    ReturnValues="UPDATED_NEW"
                )
            entity = Table.get_item( Key={ 'name': 'game' })
            ammo = entity['Item']['userBullets']
            formatAPL(action,ammo)
            
        
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False).add_directive(
                RenderDocumentDirective(
                    document=_load_apl_document("/tmp/layout.json")
                )
            )
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Reload to get more ammo, block to stop incoming fire, and shoot to kill!"

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
                "Hello World", speech_text))
        return handler_input.response_builder.response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "All in a day's work!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text))
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "We dont speak that jargon here."
        reprompt = "Try saying reload, sheild, or shoot"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "My gun's jammed, try restarting the game."
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ReloadIntentHandler())
sb.add_request_handler(ShootIntentHandler())
sb.add_request_handler(SheildIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
