# llm/factory.py
class LLMFactory:
    """Factory for creating LLMs for specific tasks."""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.instances = {}
        
    def get_llm(self, task_name):
        """Get the appropriate LLM for a specific task."""
        if task_name in self.instances:
            return self.instances[task_name]
            
        task_config = self.config.get(task_name, self.config.get("default"))
        llm = self._create_llm_instance(task_config)
        self.instances[task_name] = llm
        return llm
        
    def _create_llm_instance(self, config):
        """Create an LLM instance based on configuration."""
        provider = config.get("provider", "ollama")
        model = config.get("model", "llama3")
        
        if provider == "ollama":
            from .ollama import OllamaLLM
            return OllamaLLM(model=model, **config)
        elif provider == "openai":
            from .openai import OpenAILLM
            return OpenAILLM(model=model, **config)
        # Add other providers as needed
            
    def _default_config(self):
        """Return default LLM configurations."""
        return {
            "default": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "contextualize": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.5,
                "max_tokens": 2000
            },
            "clarify": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "categorize": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.3,
                "max_tokens": 2000
            },
            "crystallize": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "connect": {
                "provider": "ollama",
                "model": "llama3",
                "temperature": 0.5,
                "max_tokens": 2000
            }
        }