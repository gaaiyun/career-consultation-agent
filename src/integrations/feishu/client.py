from __future__ import annotations


class FeishuBitableClient:
    def __init__(self, app_token: str = "", table_id: str = "", tenant_access_token: str = "") -> None:
        self.app_token = app_token
        self.table_id = table_id
        self.tenant_access_token = tenant_access_token

    def is_configured(self) -> bool:
        return bool(self.app_token and self.table_id and self.tenant_access_token)

    def sync_record(self, payload: dict) -> dict:
        raise NotImplementedError("Feishu sync is reserved for a later version.")
