import json
from typing import Any, Callable, Dict

from airflow.models.baseoperator import BaseOperator
from airflow.utils.context import Context
from pulumi import automation as auto

from pulumi_provider.hooks.pulumi_auto import PulumiHook


class BasePulumiOperator(BaseOperator):
    def __init__(
        self,
        *args,
        project_name: str,
        stack_name: str,
        pulumi_program: Callable,
        stack_config: Dict[str, Any] = None,
        plugins: Dict[str, str] = None,
        pulumi_conn_id: str = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.project_name = project_name
        self.stack_name = stack_name
        self.pulumi_program = pulumi_program
        self.stack_config = stack_config or {}
        self.plugins = plugins or {}
        self.pulumi_conn_id = pulumi_conn_id
        self.stack: auto.Stack = None
        self.hook = PulumiHook(
            project_name=self.project_name,
            stack_name=self.stack_name,
            pulumi_program=self.pulumi_program,
            pulumi_conn_id=self.pulumi_conn_id,
        )

    def pre_execute(self, context: Any):
        self.stack = self.hook.get_conn()
        for plugin, version in self.plugins.items():
            self.stack.workspace.install_plugin(plugin, version)

        for key, value in self.stack_config.items():
            self.stack.set_config(key, auto.ConfigValue(value))
        return super().pre_execute(context)


class PulumiPreviewOperator(BasePulumiOperator):
    def execute(self, context: Context) -> Any:
        result = self.stack.preview(on_output=self.log.info)
        self.log.info(
            f"preview summary: \n{json.dumps(result.change_summary, indent=4)}"
        )


class PulumiUpOperator(BasePulumiOperator):
    def execute(self, context: Context) -> Any:
        result = self.stack.up(on_output=self.log.info)
        self.log.info(
            f"update summary: \n{json.dumps(result.summary.resource_changes, indent=4)}"
        )


class PulumiDestroyOperator(BasePulumiOperator):
    def execute(self, context: Context) -> Any:
        result = self.stack.destroy(on_output=self.log.info)
        self.log.info(
            f"destroy summary: \n{json.dumps(result.summary.resource_changes, indent=4)}"
        )