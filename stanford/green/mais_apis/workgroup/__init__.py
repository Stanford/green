"""Python wrapper around MaIS Workgroup API"""

from stanford.green.mais_apis import MaIS_API

## TYPING
from typing import Any, cast
## END OF TYPING

class WorkgroupAPI(MaIS_API):

    def __init__(
            self,
            base_url:  str,
            cert_path: str,
            key_path:  str,
            name:      str
    ):
        super().__init__(base_url=base_url, cert_path=cert_path, key_path=key_path)

        self.name = name

    def __str__(self) -> str:
        fields = []
        fields.append(f"workgroup name: {self.name}")
        fields.append(f"base URL: {self.base_url}")

        return f"<{','.join(fields)}>"

    def search(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def get(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def create(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def update(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def delete(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def list_members(self) -> list[str]:
        """Return a list of members.
        """
        url_suffix = f"{self.name}/privgroup?role=MEMBERS"
        response = self.GET(url_suffix)

        response.raise_for_status()

        response_json = response.json()
        if ('members' not in response_json):
            return []

        members_data = response_json['members']

        members = []
        for member_data in members_data:
            if ('id' in member_data):
                id = member_data['id']
                members.append(id)
            else:
                msg = f"member data '{member_data}' missing required variable 'id'"
                raise ValueError(msg)

        return members

    def list_admins(self) -> None:
        """Return a list of admins.
        """
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def add_user(self, user: str) -> dict[str, Any]:
        """Add a user to the workgroup.

        user should be a sunetid.
        """
        url_suffix = f"{self.name}/members/{user}?type=USER"
        response = self.PUT(url_suffix)

        response.raise_for_status()

        return cast(dict[str, Any], response.json())

    def add_workgroup(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def add_admin(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def remove_user(self, user: str) -> dict[str,Any]:
        """Remove a user from the workgroup.

        user should be a sunetid.
        """
        url_suffix = f"{self.name}/members/{user}?type=USER"
        response = self.DELETE(url_suffix)

        response.raise_for_status()

        return cast(dict[str, Any], response.json())

    def remove_workgroup(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def remove_admin(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def get_integration(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def add_integration(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)

    def remove_integration(self) -> None:
        msg = "this method has not yet been implemented"
        raise NotImplementedError(msg)


