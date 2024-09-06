from flask import Flask, request, jsonify
import json
import time
import threading
import requests
import uuid
import datetime
import os
import json
from dotenv import load_dotenv
app = Flask(__name__)
from flask_mysqldb import MySQL
from utils.version import API_VERSION, SERVICE_NAME
from utils.status_codes import StatusCodes
from uuid import uuid4
from api.models import AudioCraftRequestCall,AudioCraftRequestResult, response_template

from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from crewai import Crew, Process
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()  # Take environment variables from.env.
app.config.from_object(__name__)  # Load config from object



SERPER_API_KEY = os.getenv('SERPER_API_KEY')
llm = ChatGroq(groq_api_key=os.getenv('GROQ_API_KEY'), model='llama-3.1-70b-versatile', temperature=0.1)

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

# Load JSON configuration
with open('config.json') as f:
    config = json.load(f)

############### ENV VARIABLES ###############
SUPPORTED_METHOD = ["example_method"]#["AudioCraft"]
PROMT_LEN = 10
MAX_DURATION = 10


############### ADD YOUR AI MARKETPLACE WEBHOOK ENDPOINT HERE ###############
webhook_url = "http://localhost:8000/callback"
# webhook_url = "https://marketplace-api-user.dev.devsaitech.com/api/v1/ai-connection/callback"


############### ADD YOUR CUSTOM AI AGENT CALL HERE ###############
def hello_world():
    stock_selection = "AAPL"
    start_time = time.time()

    data_analyst_agent = Agent(
        role="Data Analyst",
        goal="Monitor and analyze market data in real-time "
             "to identify trends and predict market movements.",
        backstory="Specializing in financial markets, this agent "
                  "uses statistical modeling and machine learning "
                  "to provide crucial insights. With a knack for data, "
                  "the Data Analyst Agent is the cornerstone for "
                  "informing trading decisions.",
        verbose=True,
        allow_delegation=True,
        tools=[scrape_tool, search_tool],
        llm=llm,
    )

    trading_strategy_agent = Agent(
        role="Trading Strategy Developer",
        goal="Develop and test various trading strategies based "
             "on insights from the Data Analyst Agent.",
        backstory="Equipped with a deep understanding of financial "
                  "markets and quantitative analysis, this agent "
                  "devises and refines trading strategies. It evaluates "
                  "the performance of different approaches to determine "
                  "the most profitable and risk-averse options.",
        verbose=True,
        allow_delegation=True,
        tools=[scrape_tool, search_tool],
        llm=llm,
    )

    # Task for Data Analyst Agent: Analyze Market Data
    data_analysis_task = Task(
        description=(
            "Continuously monitor and analyze market data for "
            "the selected stock ({stock_selection}). "
            "Use statistical modeling and machine learning to "
            "identify trends and predict market movements."
        ),
        expected_output=(
            "Insights and alerts about significant market "
            "opportunities or threats for {stock_selection}."
        ),
        agent=data_analyst_agent,
    )

    # Task for Trading Strategy Agent: Develop Trading Strategies
    strategy_development_task = Task(
        description=(
            "Develop and refine trading strategies based on "
            "the insights from the Data Analyst and "
            # "user-defined risk tolerance ({risk_tolerance}). "
            # "Consider trading preferences ({trading_strategy_preference})."
        ),
        expected_output=(
            "A set of potential trading strategies for {stock_selection} "
            "that align with the user's risk tolerance."
        ),
        agent=trading_strategy_agent,
    )

    # Define the crew with agents and tasks
    financial_trading_crew = Crew(
        agents=[
            data_analyst_agent,
            trading_strategy_agent,
            # execution_agent,
            # risk_management_agent
        ],

        tasks=[
            data_analysis_task,
            strategy_development_task,
            # execution_planning_task,
            # risk_assessment_task
        ],

        manager_llm=llm,
        process=Process.sequential,
        verbose=True,
    )

    result = financial_trading_crew.kickoff(inputs={
        'stock_selection': stock_selection,
        # 'initial_capital': initial_capital,
        # 'risk_tolerance': risk_tolerance,
        # 'trading_strategy_preference': trading_strategy_preference,
        # 'news_impact_consideration': news_impact_consideration
    })

    time.sleep(5)  # Placeholder for actual task processing
    end_time = time.time()
    processing_duration = end_time - start_time  # Calculate processing duration in seconds
    return str(result), processing_duration



############### CHECK IF ALL INFORMATION IS IN REQUEST ###############
def check_input_request(request):
    reason = ""
    status = ""
    user_id = request.headers.get('X-User-ID', None)
    if user_id is None or not user_id.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "userToken is invalid"
    request_id = request.headers.get('x-request-id', None)
    request_data = request.get_json()
    print(request_data)
    respose_data = None

    method = request_data['method']
    print(method)
    if request_id is None or not request_id.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "requestId is invalid"
    if method is None or not method.strip():
        status = StatusCodes.INVALID_REQUEST
        reason = "method is invalid"
    elif method not in SUPPORTED_METHOD:
        status = StatusCodes.UNSUPPORTED
        reason = f"unsupported method {method}"
    if status != "":
        trace_id = uuid4().hex
        error_code = {
            "status": status,
            "reason": reason
        }
        respose_data = response_template(request_id, trace_id, -1,True, {}, error_code)
        
    return respose_data

############### API ENDPOINT TO RECEIVE REQUEST ###############
@app.route('/call', methods=['POST'])
def call_endpoint():
    user_id = request.headers.get('X-User-ID', None)

    ret = check_input_request(request)
    if ret is not None:
        return ret

    task_id = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    # Response preparation
    response = {"taskId": task_id}
    error_code = {"status": StatusCodes.PENDING, "reason": "Pending"}
    respose_data = response_template(requestId, trace_id, -1, False, response, error_code)

    # Task processing in a separate thread
    threading.Thread(target=process_task, args=(task_id,requestId,user_id,)).start()

    # Immediate response to the client
    return jsonify(respose_data), 200


############### PROCESS THE CALL TASK HERE ###############
def success_response(task_id, data, dataType, requestId, trace_id, process_duration):
        # Prepare the response
        response = {
            "taskId": task_id,  # Assuming task_id is defined somewhere
            "data": data,
            "dataType": dataType
        }
        error_code = {"status": StatusCodes.SUCCESS, "reason": "success"}
        response_data = response_template(requestId, trace_id, process_duration, True, response, error_code)
        return response_data



def process_task(task_id,requestId, user_id):
    data, processing_duration = hello_world()
    print(data)
    # Send the callback
    send_callback(user_id, task_id,requestId,processing_duration, data)

            
############### SEND CALLBACK TO YOUR APP MARKETPLACE ENDPOINT WITH TASK RESPONSE ###############
def send_callback(user_id, task_id,requestId, processing_duration, data):
    
    callback_message = {
        "apiVersion": API_VERSION,
        "service": SERVICE_NAME,
        "datetime": datetime.datetime.now().isoformat(),
        "processDuration": processing_duration,  # Simulated duration
        "taskId": task_id,
        "isResponseImmediate": False,
        "response": {
            "dataType": "META_DATA",
            "data": data
        },
        "errorCode": {
            "status": "TA_000",
            "reason": "success"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-marketplace-token": "1df239ef34d92aa8190b8086e89196ce41ce364190262ba71964e9f84112bc45",
        "x-request-id": requestId,
        "x-user-id": user_id
    }

    response = requests.post(webhook_url, json=callback_message, headers=headers)





############### WHEN THIS API ENDPOINT IS PINGED WITH A TASKID IT RETURNS THE TASK STATUS AND DATA ###############

###### USE YOUR OWN DATABASE TO STORE TASKID : RESULT ######
@app.route('/result', methods=['POST'])
def result():
    user_id = request.headers.get('X-User-ID', None)
    requestId = request.headers.get('x-request-id', None)
    request_data = request.get_json()
    taskID = request_data.get("taskId")
    trace_id = str(uuid.uuid4())
    result_request_id = str(uuid.uuid4())
    if user_id is None or not user_id.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No User ID found in headers"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data

    if requestId is None or not requestId.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No request ID found in headers"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data
    
    if taskID is None or not taskID.strip():
        error_code = {"status": StatusCodes.ERROR, "reason": "No task ID found in body"}
        response_data = response_template(result_request_id, trace_id, -1, True, {}, error_code)
        return response_data

    # print(taskID)
    data = {
        "dataType": 'META_DATA',
        "data": "stored-data"
    }
    response_data = success_response(
        taskID, data, requestId, trace_id, -1
    )
    # print(data)
    return jsonify(response_data), 200




############### RUN YOUR SERVER HERE ###############
if __name__ == '__main__':
    app.run(debug=True)
