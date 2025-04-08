import os
import json
from typing import ClassVar, List
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
import re
from typing import List, Union
from agents.outreach_agent import OutreachSequenceGenerator
from models.database import get_db_connection


# debuggng
# import langchain
# langchain.debug = True
class CustomReActOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        print("=====inside custom parser=====")
        print(f"LLM Output: {llm_output}")
        if "Final Answer:" in llm_output:
            final_answer_text = llm_output.split("Final Answer:")[-1].strip()
            if final_answer_text.strip().startswith("{"):
                try:
                    return_values = json.loads(final_answer_text)
                    return AgentFinish(
                        return_values=return_values,
                        log=llm_output,
                    )
                except json.JSONDecodeError:
                    pass
            
            return AgentFinish(
                return_values={"output": final_answer_text},
                log=llm_output,
            )
            # return AgentFinish(
            #     return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
            #     log=llm_output,
            # )
        print("==== NO MATCH ====")
        regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)

        if not match:
            return AgentAction(tool="General_Conversation", tool_input=llm_output, log=llm_output)
        
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        
        action = match.group(1).strip()
        action_input = match.group(2).strip()
        
        # Return the action
        return AgentAction(tool=action, tool_input=action_input, log=llm_output)

class HRAgentPrompt(StringPromptTemplate):
    template: ClassVar[str] = """You are an AI assistant for HR professionals, specializing in talent acquisition.

        Current conversation:
        {chat_history}

        User: {input}

        You have access to the following tools:
        {tools}

        Focus on the user's request and decide which tool to use.
        If the user is asking for help with a specific outreach sequence, use the "Generate_Outreach_Sequence" tool.
        If the user is asking to edit, modify, change, update, revise, improve, or customize an existing outreach sequence,
        use the "Edit_Sequence" tool.
        If the user is asking for best practices in talent outreach, use the "Search_Best_Practices" tool.
        If the user is asking a general question or making a casual comment, use the "General_Conversation" tool.
        If you are unsure, use the "General_Conversation" tool to respond conversationally.

        Use the following format:
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)  

        Critical Formatting Rules:
        1. Always use EXACTLY ONE newline between components
        2. Final Answer must be on its own line
        3. Never combine multiple components in one line
        4. Action Input must be quoted if containing spaces

        Example of BAD formatting:
        Thought: I think Action: Generate_Outreach Action Input: test

        Example of GOOD formatting:
        Thought: I should generate an outreach sequence
        Action: Generate_Outreach_Sequence
        Action Input: "campaign requirements for engineers for campaign_id: 123"
        Final Answer: Here is the outreach sequence based on your requirements

        Example for EDIT requests:
        Thought: The user wants to edit an existing sequence
        Action: Edit_Sequence
        Action Input: "edit sequence_id: 25 for campaign_id: 4 to be more casual"
        Final Answer: Here is the edited sequence based on your requirements

        Begin!"""
    
    input_variables: List[str] = ["input", "chat_history"]
    tools: List[Tool] = []
    def __init__(self, tools: List[Tool], **kwargs):
        super().__init__(**kwargs)
        print(f"Initalizing with {tools}")
        self.tools = tools

    def format(self, **kwargs):
        tools = kwargs.get("tools", self.tools)
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

class HRAgent:
    def __init__(self):
        # self.llm = OpenAI(temperature=0.7)
        self.llm =ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)
        self.outreach_generator = OutreachSequenceGenerator()
        # tools
        self.tools = [
            Tool(
                name="Generate_Outreach_Sequence",
                func=self.generate_sequence,
                description="Generate an outreach sequence for campaign_id based on campaign requirements"
            ),
            Tool(
                name="Edit_Sequence",
                func=self.edit_sequence,
                description="IMPORTANT: Use this tool for ANY request to edit, modify, change, update, revise, improve, or customize an existing outreach sequence. If the user mentions any of these words in relation to a sequence, ALWAYS use this tool."
            ),
            Tool(
                name="Search_Best_Practices",
                func=self.search_best_practices,
                description="Search for best practices in talent outreach"
            ),
            Tool(
                name="General_Conversation",
                func=self.handle_general_conversation,
                description="Only handle general conversation if any other tool is not applicable. This is a fallback tool."
            )
        ]
        
        # agent
        prompt = HRAgentPrompt(
            tools=self.tools,
            input_variables=["input", "chat_history"]
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        self.agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            allowed_tools=[tool.name for tool in self.tools],
            output_parser=CustomReActOutputParser(),
            stop=["Observation:", "Final Answer:"]
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=1,
            early_stopping_method="force",
            handle_parsing_errors=self.handle_parsing_errors,
            input_key="input",
            return_intermediate_steps=True
        )

    def _parse_requirements(self, requirements_text):
        """Parse natural language requirements into structured data"""
        
        prompt = f"""
        Extract the following information from this text:
        - target_role
        - industry
        - company_values
        - unique_selling_points
        
        Text: {requirements_text}
        
        Return as a JSON object with these keys.
        """
        response = self.llm.invoke(prompt)
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # If no JSON found in markdown format, try to parse the whole response
            return json.loads(response)
        except:
            # Fallback to basic extraction
            info = {
                "target_role": "",
                "industry": "",
                "company_values": "",
                "unique_selling_points": ""
            }
            
            # Simple extraction
            if "target role" in requirements_text.lower():
                role_match = re.search(r'target role[:\s]+([^,\n.]+)', requirements_text, re.IGNORECASE)
                if role_match:
                    info["target_role"] = role_match.group(1).strip()
                    
            if "industry" in requirements_text.lower():
                industry_match = re.search(r'industry[:\s]+([^,\n.]+)', requirements_text, re.IGNORECASE)
                if industry_match:
                    info["industry"] = industry_match.group(1).strip()
            
            # Use the whole text as values if nothing extracted
            if not any(info.values()):
                info["company_values"] = requirements_text[:100]
                info["unique_selling_points"] = "From requirements"
                
            return info

    def generate_sequence(self, requirements):
        """Generate an outreach sequence based on campaign requirements"""
        try:
            print(f"Generating sequence with requirements: {requirements}")
            og_requirements = requirements

            if isinstance(requirements, str):
                campaign_id = None
                campaign_match = re.search(r"campaign(?:_id| id|ID)[: ]*(\d+)", requirements)
                if campaign_match:
                    campaign_id = int(campaign_match.group(1))
                campaign_info = self._parse_requirements(requirements)
            else:
                campaign_info = og_requirements
                campaign_id = None

            sequence = self.outreach_generator.generate_sequence(campaign_info)

            sequence_id = None
            try:
                if not campaign_id:
                    campaign_id = self._extract_campaign_id_from_memory()
                
                if campaign_id:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO outreach_sequences (campaign_id, sequence_data, version) VALUES (%s, %s, %s) RETURNING id",
                        (campaign_id, json.dumps(sequence), 1)
                    )
                    sequence_id = cur.fetchone()['id']
                    conn.commit()
                    cur.close()
                    conn.close()
            except Exception as e:
                print(f"Error saving sequence: {str(e)}")
           
            sequence_json = json.dumps(sequence, indent=2)
            final_answer = {
                        "output": sequence_json,
                        "action_tool": "Generate_Outreach_Sequence",
                        "message": f"Generating Sequence..."
                    }
            if campaign_id:
                final_answer["campaign_id"] = campaign_id
            if sequence_id:
                final_answer["sequence_id"] = sequence_id
                final_answer["message"] += f" (ID: {sequence_id})"
                
            return f"Final Answer: {json.dumps(final_answer)}"
        except Exception as e:
            return f"Error generating sequence: {str(e)}"
    
    def edit_sequence(self, edit_request):
        """Edit an existing outreach sequence based on user feedback"""
        try:
            sequence_id = None
            campaign_id = None
            
            if isinstance(edit_request, str):
                id_match = re.search(r"sequence (?:id|ID)[: ]*(\d+)", edit_request)
                if id_match:
                    sequence_id = int(id_match.group(1))
                else:
                    campaign_match = re.search(r"campaign(?:_id| id|ID)[: ]*(\d+)", edit_request)
                    if campaign_match:
                        campaign_id = int(campaign_match.group(1))
                
                conn = get_db_connection()
                cur = conn.cursor()
                
                if sequence_id:
                    cur.execute("SELECT id, sequence_data, campaign_id, version FROM outreach_sequences WHERE id = %s", (sequence_id,))
                elif campaign_id:
                    cur.execute("""
                        SELECT id, sequence_data, campaign_id, version 
                        FROM outreach_sequences 
                        WHERE campaign_id = %s 
                        ORDER BY version DESC, created_at DESC 
                        LIMIT 1
                    """, (campaign_id,))
                else:
                    # fallback
                    campaign_id = self._extract_campaign_id_from_memory()
                    if campaign_id:
                        cur.execute("""
                            SELECT id, sequence_data, campaign_id, version 
                            FROM outreach_sequences 
                            WHERE campaign_id = %s 
                            ORDER BY version DESC, created_at DESC 
                            LIMIT 1
                        """, (campaign_id,))
                    else:
                        cur.close()
                        conn.close()
                        return "To edit an existing sequence, please provide a sequence ID or campaign ID in your request."
                
                result = cur.fetchone()
                if result:
                    sequence_id = result['id']
                    sequence_json = result['sequence_data']
                    campaign_id = result['campaign_id']
                    version = result['version']
                    
                    if isinstance(sequence_json, str):
                        sequence = json.loads(sequence_json)
                    else:
                        sequence = sequence_json
                        
                    edited_sequence = self.outreach_generator.edit_sequence(sequence, edit_request)
                    
                    cur.execute(
                        "INSERT INTO outreach_sequences (campaign_id, sequence_data, version) VALUES (%s, %s, %s) RETURNING id",
                        (campaign_id, json.dumps(edited_sequence), version + 1)
                    )
                    new_sequence_id = cur.fetchone()['id']
                    conn.commit()
                    
                    cur.close()
                    conn.close()
                    
                    edited_json = json.dumps(edited_sequence, indent=2)
                    final_answer = {
                        "output": edited_json,
                        "action_tool": "Edit_Sequence",
                        "message": f"Updated sequence..."
                    }
                    if campaign_id:
                        final_answer["campaign_id"] = campaign_id
                        final_answer["message"] += f" (Campaign ID: {campaign_id})"
                    if new_sequence_id:
                        final_answer["sequence_id"] = new_sequence_id
                        final_answer["message"] += f" (ID: {new_sequence_id})"
                    
                    return f"Final Answer: {json.dumps(final_answer)}"
                    # final_answer = {
                    #     "output": edited_json,
                    #     "action_tool": "Edit_Sequence",
                    #     "sequence_id": new_sequence_id,
                    #     "campaign_id": campaign_id,
                    #     "message": f"I've updated the sequence (new ID: {new_sequence_id}) for campaign {campaign_id}. You can reference this ID for future edits."
                    # }
                    # return f"Here is the edited sequence (ID: {new_sequence_id}): {edited_json}\n\nFinal Answer: {final_answer} "
                    # return f"Here is the edited sequence (ID: {new_sequence_id}): {edited_json}\n\nFinal Answer: {final_answer} I've updated the sequence (new ID: {new_sequence_id}) for campaign {campaign_id}. You can reference this ID for future edits."
                else:
                    cur.close()
                    conn.close()
                    error_message = ""
                    if sequence_id:
                        error_message = f"Error: Sequence with ID {sequence_id} was not found."
                    elif campaign_id:
                        error_message = f"Error: No sequences found for campaign ID {campaign_id}."
                    else:
                        error_message = "Error: I couldn't identify which sequence to edit. Please provide a sequence ID or campaign ID."
                    final_answer = {
                        "output": "",
                        "action_tool": "Edit_Sequence",
                        "message": error_message,
                        "error": True
                    }
                    return f"Final Answer: {json.dumps(final_answer)}"
                        
            final_answer = {
                "output": "",
                "action_tool": "Edit_Sequence",
                "message": "To edit an existing sequence, please provide the sequence ID (e.g., 'Edit sequence ID 123') or campaign ID (e.g., 'Edit sequence for campaign 456').",
                "error": True
            }
            return f"Final Answer: {json.dumps(final_answer)}"
        except Exception as e:
            final_answer = {
                "output": "",
                "action_tool": "Edit_Sequence",
                "message": f"Error editing sequence: {str(e)}",
                "error": True
            }
            return f"Final Answer: {json.dumps(final_answer)}"
    
    def chat(self, user_input, conversation_id=None):
        """Process user input and return agent response"""
        try:
            print(f"====IN CHAT======")
            print(f"User input: {user_input}")

            if conversation_id:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT messages FROM conversations WHERE id = %s", (conversation_id,))
                conversation = cur.fetchone()
                cur.close()
                conn.close()
                
                if conversation:
                    self.memory.clear()
                    
                    messages = conversation['messages']
                    for msg in messages:
                        if msg['role'] == 'user':
                            self.memory.chat_memory.add_user_message(msg['content'])
                        else:
                            content = msg['content']
                            if isinstance(content, dict):
                                content = json.dumps(content)
                            self.memory.chat_memory.add_ai_message(content)
            print(f"=== Fetched conversation ===")
            print(f"====Execting AGENT====")

            result = self.agent_executor.invoke({"input": user_input})
            
            # print(f"Agent result: {result}")

            if "intermediate_steps" in result and len(result["intermediate_steps"]) > 0:
                last_step = result["intermediate_steps"][-1]
                action = last_step[0] 
                tool_output = last_step[1] 
                
                if isinstance(tool_output, str) and "Final Answer:" in tool_output:
                    tool_output = tool_output.split("Final Answer:")[1].strip()
                    try:
                        return json.loads(tool_output)
                    except json.JSONDecodeError:
                        return {
                            "output": "Response processed",
                            "action_tool": action.tool,
                            "message": tool_output,
                            "error": True
                        }
                return {
                    "output": "Response generated",
                    "action_tool": action.tool,
                    "message": tool_output if isinstance(tool_output, str) else json.dumps(tool_output)
                }
                
            return {
                "output": "Response generated",
                "action_tool": "Unknown",
                "message": result.get("output", "No response generated"),
            }
                # return tool_output
                # return result.get("output", "No response generated")
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print(f"====Defaulting to general conversation")
            general_response = self.handle_general_conversation(user_input)

            if isinstance(general_response, str) and "Final Answer:" in general_response:
                json_str = general_response.split("Final Answer:")[1].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
                    
            return {
                "output": f"Error processing request: {str(e)}", 
                "action_tool": "General_Conversation",
                "message": "I'm here to help with your HR and talent acquisition needs. How can I assist you today?",
                "error": True
            }
            # return self.handle_general_conversation(user_input)
    
    def _extract_campaign_id_from_memory(self):
        """Extract campaign ID from conversation memory"""
        try:
            if hasattr(self, 'memory') and hasattr(self.memory, 'chat_memory'):
                memory_string = str(self.memory.chat_memory)
                print(f"\n\nMemory string: {memory_string}")
                campaign_match = re.search(r"Working on campaign.*?campaign_id[: ]*(\d+)", memory_string)
                if campaign_match:
                    return int(campaign_match.group(1))
                    
                id_match = re.search(r"campaign_id[: ]*(\d+)", memory_string)
                if id_match:
                    return int(id_match.group(1))
        except Exception as e:
            print(f"Error extracting campaign ID: {str(e)}")
        return None

    def search_best_practices(self, query):
        """Search for best practices in talent outreach"""
        # print(f"Searching best practices for query: {query}")
        
        prompt = f"""
        Generate a concise and specific best practice for talent outreach based on this query:
        
        Query: {query}
        
        Your response should:
        1. Be specific and actionable
        2. Include a percentage or metric if relevant
        3. Be formatted as a single best practice tip
        4. Be between 50-150 words
        """
        
        try:
            response = self.llm.invoke(prompt).content
            final_answer = {
                "output": "Best practice for talent outreach",
                "action_tool": "Search_Best_Practices",
                "message": response,
            }
            
            return f"Final Answer: {json.dumps(final_answer)}"
        except Exception as e:
            best_practice = "[Best Practice] Personalized messages referencing specific achievements boost response rates by 30%."
        
            final_answer = {
                "output": f"Error retrieving additional practices: {str(e)}",
                "action_tool": "Search_Best_Practices",
                "message": best_practice,
                "error": True
            }
            
            return f"Final Answer: {json.dumps(final_answer)}"
        
    def handle_general_conversation(self, input_text):
        """Handle general conversation that doesn't require specific tools"""
        prompt = f"""
        The user has sent the following message in a conversation about HR and talent acquisition:
        
        {input_text}
        
        Respond naturally and conversationally as an HR assistant. If this is a greeting, respond appropriately.
        If the user seems to be asking for help but in an informal way, gently guide them toward how you can
        help with talent acquisition tasks like creating outreach sequences.
        Limit your response to 50-150 words.
        """
        
        try:
            response = self.llm.invoke(prompt).content
            final_answer = {
                "message": response,
                "action_tool": "General_Conversation",
                "output": "Conversation response"
            }
            
            return f"Final Answer: {json.dumps(final_answer)}"
            # return response
        except Exception as e:
            default_response = "I'm here to help with your HR and talent acquisition needs. How can I assist you today?"
            
            final_answer = {
                "output": "Conversation response",
                "action_tool": "General_Conversation",
                "message": default_response,
                "error": True
            }
            
            return f"Final Answer: {json.dumps(final_answer)}"
        
    def handle_parsing_errors(self, error):
            """Handle parsing errors by treating them as conversational responses"""
            error_text = str(error)
            match = re.search(r"Could not parse LLM output: `(.*)`", error_text, re.DOTALL)
            if match:
                llm_text = match.group(1).strip()
                if "Thought:" in llm_text:
                    thought_match = re.search(r"Thought: (.*?)$", llm_text, re.DOTALL)
                    if thought_match:
                        conversation_text = thought_match.group(1).strip()
                        return self.handle_general_conversation(conversation_text)
                return self.handle_general_conversation(llm_text)
            return "I'm here to help with your HR and talent acquisition needs. How can I assist you today?"
    



