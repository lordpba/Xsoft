import logging
from typing import Optional
from backend.core.llm import LLMClient
from backend.core.prompts import SYSTEM_PROMPTS

logger = logging.getLogger("xsoft.agent")

class Agent:
    def __init__(self, role: str, llm_client: LLMClient):
        self.role = role
        self.llm_client = llm_client
        self.system_prompt = SYSTEM_PROMPTS.get(role, f"Sei un agente specializzato in {role}.")
        logger.info(f"Agente [{self.role}] caricato con successo.")

    async def run(self, prompt: str) -> str:
        logger.info(f"Esecuzione agente [{self.role}]...")
        response = await self.llm_client.generate(prompt, system_instruction=self.system_prompt)
        logger.info(f"Agente [{self.role}] ha risposto con successo.")
        return response
