from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    image_static_path: str
    allowed_ips: str

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def allowed_ip_set(self) -> set[str]:
        return {ip.strip() for ip in self.allowed_ips.split(",")}

settings = Settings()
