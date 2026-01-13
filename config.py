"""
Configuration management for the CDKG system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class Neo4jConfig(BaseModel):
    """Neo4j connection configuration"""
    uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))
    
    def validate(self) -> bool:
        """Check if configuration is valid"""
        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD not set in .env file!\n"
                "Please set your Neo4j Desktop password in .env"
            )
        return True


class EmbeddingConfig(BaseModel):
    """Embedding model configuration"""
    model_name: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    )
    device: str = "cpu"  # Can be changed to "cuda" if GPU available
    batch_size: int = 32
    max_length: int = 512


class LLMConfig(BaseModel):
    """LLM configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2048
    temperature: float = 0.7
    
    def validate(self) -> bool:
        """Check if API key is set"""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set in .env file!\n"
                "Get your API key from: https://console.anthropic.com/"
            )
        return True


class PathConfig(BaseModel):
    """Path configuration"""
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent)
    data_dir: Path = Field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    embeddings_dir: Path = Field(default_factory=lambda: Path(os.getenv("EMBEDDINGS_DIR", "embeddings")))
    
    def __init__(self, **data):
        super().__init__(**data)
        # Make paths absolute
        if not self.data_dir.is_absolute():
            self.data_dir = self.base_dir / self.data_dir
        if not self.embeddings_dir.is_absolute():
            self.embeddings_dir = self.base_dir / self.embeddings_dir
    
    def ensure_dirs(self):
        """Create directories if they don't exist"""
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def cdl_db_path(self) -> Path:
        """Path to cdl_db directory"""
        return self.data_dir / "cdl_db"


class Config(BaseModel):
    """Main configuration class"""
    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    
    def validate_all(self):
        """Validate all configurations"""
        print("🔍 Validating configuration...")
        
        # Check Neo4j
        try:
            self.neo4j.validate()
            print("  ✅ Neo4j config valid")
        except ValueError as e:
            print(f"  ❌ Neo4j config invalid: {e}")
            raise
        
        # Check LLM
        try:
            self.llm.validate()
            print("  ✅ LLM config valid")
        except ValueError as e:
            print(f"  ❌ LLM config invalid: {e}")
            raise
        
        # Check paths
        self.paths.ensure_dirs()
        print(f"  ✅ Paths configured:")
        print(f"     Data: {self.paths.data_dir}")
        print(f"     Embeddings: {self.paths.embeddings_dir}")
        
        # Check if cdl_db exists
        if not self.paths.cdl_db_path.exists():
            print(f"  ⚠️  Warning: cdl_db not found at {self.paths.cdl_db_path}")
            print(f"     Please copy your cdl_db directory to {self.paths.data_dir}/")
        else:
            print(f"  ✅ cdl_db found at {self.paths.cdl_db_path}")
        
        print("✅ Configuration validation complete!\n")


# Global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    try:
        config.validate_all()
        print("\n✅ All configurations are valid!")
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
