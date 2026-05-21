"""
Investigation Agent module.
Multi-step reasoning agent using LangChain and OpenAI GPT-4o-mini.
Implements ReAct (Reasoning + Acting) pattern for compliance investigations.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.schema import SystemMessage
from security.llm_guard import LLMGuard
from core.splunk_tools import SplunkTools
from core.rag_tools import ComplianceRAG


class InvestigationAgent:
    """
    AI-powered compliance investigation agent.
    Uses multi-step reasoning with access to Splunk data and compliance regulations.
    """
    
    SYSTEM_PROMPT = """You are a financial compliance expert tasked with investigating suspicious transactions.

Your role:
1. Gather data methodically about the user and their transaction history
2. Identify anomalies against normal patterns
3. Reference relevant compliance regulations
4. Provide risk assessment and recommendations
5. NEVER make absolute judgments or legal conclusions

Important constraints:
- You CANNOT conclude guilt or criminal activity
- You CANNOT authorize freezing accounts or taking enforcement actions
- You MUST cite specific regulations when recommending escalation
- Present only factual observations and compliance concerns
- All findings require human analyst review

Investigation steps:
1. Get user profile to establish baseline
2. Review recent transactions for anomalies
3. Check device history for unusual access patterns
4. Search compliance regulations for relevant rules
5. Synthesize findings into risk-based recommendation

Format your final response with:
- **Risk Score**: (Low/Medium/High/Critical)
- **Anomalies Detected**: (list with data)
- **Compliance Basis**: (relevant regulations)
- **Recommended Action**: (human review required)
"""
    
    def __init__(
        self,
        splunk_tools: SplunkTools,
        rag_tools: ComplianceRAG,
        llm_guard: LLMGuard
    ):
        """
        Initialize investigation agent with security components.
        
        Args:
            splunk_tools: SplunkTools instance for data access
            rag_tools: ComplianceRAG instance for regulation search
            llm_guard: LLMGuard for input/output security
        """
        self.splunk_tools = splunk_tools
        self.rag_tools = rag_tools
        self.llm_guard = llm_guard
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistency
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=30
        )
        
        # Create tools for agent
        self.tools = self._create_tools()
        
        # Initialize agent
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.REACT_DOCSTRING,
            verbose=True,
            max_iterations=8,
            early_stopping_method="force"
        )
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools available to the agent.
        
        Returns:
            List of LangChain Tool objects
        """
        tools = [
            Tool(
                name="get_user_profile",
                func=self._tool_get_user_profile,
                description="Get comprehensive user profile including name, email, account status, risk rating. Input: user_id"
            ),
            Tool(
                name="get_recent_transactions",
                func=self._tool_get_recent_transactions,
                description="Get recent transactions for user in past 24 hours. Shows amount, timestamp, type. Input: user_id"
            ),
            Tool(
                name="get_device_history",
                func=self._tool_get_device_history,
                description="Get device login history showing IP, device type, timestamp. Input: user_id"
            ),
            Tool(
                name="search_compliance",
                func=self._tool_search_compliance,
                description="Search compliance regulations and laws. Input: compliance topic or anomaly type"
            )
        ]
        
        return tools
    
    def _tool_get_user_profile(self, user_id: str) -> str:
        """Wrapper for SplunkTools.get_user_profile()."""
        try:
            result = self.splunk_tools.get_user_profile(user_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _tool_get_recent_transactions(self, user_id: str) -> str:
        """Wrapper for SplunkTools.get_recent_transactions()."""
        try:
            results = self.splunk_tools.get_recent_transactions(user_id, hours=24)
            return json.dumps(results, indent=2, default=str)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _tool_get_device_history(self, user_id: str) -> str:
        """Wrapper for SplunkTools.get_device_history()."""
        try:
            results = self.splunk_tools.get_device_history(user_id)
            return json.dumps(results, indent=2, default=str)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _tool_search_compliance(self, query: str) -> str:
        """Wrapper for ComplianceRAG.search()."""
        try:
            result = self.rag_tools.search(query, k=3)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def investigate(self, user_input: str) -> Dict[str, Any]:
        """
        Conduct multi-step investigation based on user query.
        
        Args:
            user_input: Investigation query (e.g., "investigate user U_12345")
            
        Returns:
            Dictionary with success status, report, and reasoning
        """
        try:
            # Validate input
            is_valid, validation_msg = self.llm_guard.validate_input(user_input)
            
            if not is_valid:
                return {
                    "success": False,
                    "report": "",
                    "reasoning": [],
                    "error": validation_msg
                }
            
            # Run agent
            print(f"\n[Agent] Starting investigation: {user_input}")
            
            response = self.agent.run(
                input=user_input,
                system_message=SystemMessage(content=self.SYSTEM_PROMPT)
            )
            
            # Sanitize output
            sanitized_report = self.llm_guard.sanitize_output(response)
            
            return {
                "success": True,
                "report": sanitized_report,
                "reasoning": self._extract_reasoning(response),
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "report": "",
                "reasoning": [],
                "error": f"Investigation failed: {str(e)}"
            }
    
    def _extract_reasoning(self, response: str) -> List[str]:
        """
        Extract reasoning steps from agent response.
        
        Args:
            response: Full agent response
            
        Returns:
            List of reasoning steps
        """
        try:
            # Simple extraction of main thoughts
            steps = []
            
            lines = response.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['thought:', 'action:', 'observation:']):
                    steps.append(line.strip())
            
            return steps if steps else [response[:200] + "..."]
        
        except Exception:
            return ["Unable to extract reasoning"]
