"""Python script execution engine for workflow tasks."""

import ast
import sys
import traceback
import asyncio
from typing import Any, Dict, Optional, Union
from datetime import datetime
import logging

from ..models.task import TaskInstance
from ..core.config import settings


class ScriptExecutionError(Exception):
    """Exception raised during script execution."""
    
    def __init__(self, message: str, line_number: Optional[int] = None, error_line: Optional[str] = None):
        super().__init__(message)
        self.line_number = line_number
        self.error_line = error_line


class ScriptEngine:
    """Python script execution engine for workflow tasks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.safe_modules = {
            'math', 'random', 'datetime', 'json', 're', 'collections', 
            'itertools', 'functools', 'operator', 'string', 'decimal'
        }
        self.safe_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'chr', 'complex', 'dict',
            'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
            'hash', 'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'map', 'max', 'min', 'next', 'oct', 'ord', 'pow', 'print',
            'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted',
            'str', 'sum', 'tuple', 'type', 'zip'
        }
    
    async def execute_script(
        self, 
        task_instance: TaskInstance, 
        script: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute Python script with task context."""
        try:
            # Validate script
            self._validate_script(script)
            
            # Prepare execution environment
            exec_globals = self._prepare_execution_environment(task_instance, context)
            
            # Execute script
            if asyncio.iscoroutinefunction(self._execute_sync_script):
                result = await self._execute_sync_script(script, exec_globals)
            else:
                result = self._execute_sync_script(script, exec_globals)
            
            # Update task output data
            if isinstance(result, dict):
                task_instance.output_data.update(result)
            else:
                task_instance.output_data['result'] = result
            
            return result
            
        except Exception as e:
            error_info = self._extract_error_info(script, e)
            raise ScriptExecutionError(
                f"Script execution failed: {str(e)}",
                line_number=error_info['line_number'],
                error_line=error_info['error_line']
            )
    
    def _validate_script(self, script: str) -> None:
        """Validate Python script syntax and security."""
        try:
            # Parse script to check syntax
            ast.parse(script)
        except SyntaxError as e:
            raise ScriptExecutionError(f"Invalid Python syntax: {e.msg}", e.lineno)
        
        # Check for potentially dangerous operations
        self._check_script_security(script)
    
    def _check_script_security(self, script: str) -> None:
        """Check script for potentially dangerous operations."""
        try:
            tree = ast.parse(script)
            
            for node in ast.walk(tree):
                # Check for import statements
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        module_name = alias.name if isinstance(node, ast.Import) else node.module
                        if module_name and not self._is_safe_module(module_name):
                            raise ScriptExecutionError(f"Import of unsafe module '{module_name}' is not allowed")
                
                # Check for function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name not in self.safe_builtins and not self._is_safe_function(func_name):
                            raise ScriptExecutionError(f"Call to unsafe function '{func_name}' is not allowed")
                
                # Check for attribute access
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        obj_name = node.value.id
                        if obj_name in ['__builtins__', '__import__', 'eval', 'exec']:
                            raise ScriptExecutionError(f"Access to unsafe attribute '{obj_name}' is not allowed")
        
        except ScriptExecutionError:
            raise
        except Exception as e:
            self.logger.warning(f"Security check failed: {e}")
    
    def _is_safe_module(self, module_name: str) -> bool:
        """Check if module is safe to import."""
        if not module_name:
            return False
        
        # Check if module is in safe list
        if module_name in self.safe_modules:
            return True
        
        # Check if it's a submodule of safe modules
        for safe_module in self.safe_modules:
            if module_name.startswith(f"{safe_module}."):
                return True
        
        return False
    
    def _is_safe_function(self, func_name: str) -> bool:
        """Check if function is safe to call."""
        # Add custom safe functions here
        custom_safe_functions = {
            'workflow_context', 'task_data', 'log_info', 'log_warning', 'log_error'
        }
        return func_name in custom_safe_functions
    
    def _prepare_execution_environment(
        self, 
        task_instance: TaskInstance, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare execution environment with task context."""
        exec_globals = {
            '__builtins__': self._get_safe_builtins(),
            '__name__': '__workflow_script__',
            '__file__': f'task_{task_instance.instance_id}',
        }
        
        # Add task context
        exec_globals.update({
            'task_id': task_instance.instance_id,
            'task_name': task_instance.task_definition.name,
            'task_type': task_instance.task_definition.task_type.value,
            'input_data': task_instance.input_data.copy(),
            'output_data': task_instance.output_data.copy(),
            'workflow_instance_id': task_instance.workflow_instance.instance_id,
        })
        
        # Add workflow context
        if context:
            exec_globals.update(context)
        
        # Add safe utility functions
        exec_globals.update(self._get_utility_functions(task_instance))
        
        return exec_globals
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get safe built-in functions and types."""
        safe_builtins = {}
        
        for name in self.safe_builtins:
            if hasattr(__builtins__, name):
                safe_builtins[name] = getattr(__builtins__, name)
        
        return safe_builtins
    
    def _get_utility_functions(self, task_instance: TaskInstance) -> Dict[str, Any]:
        """Get utility functions for script execution."""
        def log_info(message: str, **kwargs):
            """Log info message."""
            self.logger.info(f"Task {task_instance.instance_id}: {message}", extra=kwargs)
        
        def log_warning(message: str, **kwargs):
            """Log warning message."""
            self.logger.warning(f"Task {task_instance.instance_id}: {message}", extra=kwargs)
        
        def log_error(message: str, **kwargs):
            """Log error message."""
            self.logger.error(f"Task {task_instance.instance_id}: {message}", extra=kwargs)
        
        def workflow_context(key: str, default: Any = None) -> Any:
            """Get workflow context value."""
            return task_instance.workflow_instance.current_state.get(key, default)
        
        def set_workflow_context(key: str, value: Any) -> None:
            """Set workflow context value."""
            task_instance.workflow_instance.current_state[key] = value
        
        def task_data(key: str, default: Any = None) -> Any:
            """Get task data value."""
            return task_instance.input_data.get(key, default)
        
        def set_task_data(key: str, value: Any) -> None:
            """Set task data value."""
            task_instance.output_data[key] = value
        
        return {
            'log_info': log_info,
            'log_warning': log_warning,
            'log_error': log_error,
            'workflow_context': workflow_context,
            'set_workflow_context': set_workflow_context,
            'task_data': task_data,
            'set_task_data': set_task_data,
        }
    
    def _execute_sync_script(self, script: str, exec_globals: Dict[str, Any]) -> Any:
        """Execute script synchronously."""
        # Create local namespace for script execution
        exec_locals = {}
        
        # Execute script
        exec(script, exec_globals, exec_locals)
        
        # Return result if script defines one
        if 'result' in exec_locals:
            return exec_locals['result']
        
        # Return output data if script modified it
        if exec_locals.get('output_data'):
            return exec_locals['output_data']
        
        return None
    
    def _extract_error_info(self, script: str, error: Exception) -> Dict[str, Any]:
        """Extract error information from exception."""
        error_info = {
            'line_number': None,
            'error_line': None
        }
        
        try:
            if isinstance(error, SyntaxError):
                error_info['line_number'] = error.lineno
                if error.lineno and script:
                    lines = script.splitlines()
                    if 0 <= error.lineno - 1 < len(lines):
                        error_info['error_line'] = lines[error.lineno - 1]
            
            elif hasattr(error, '__traceback__'):
                # Extract line number from traceback
                tb = error.__traceback__
                while tb:
                    if tb.tb_frame.f_code.co_filename == '<string>':
                        error_info['line_number'] = tb.tb_lineno
                        if script:
                            lines = script.splitlines()
                            if 0 <= tb.tb_lineno - 1 < len(lines):
                                error_info['error_line'] = lines[tb.tb_lineno - 1]
                        break
                    tb = tb.tb_next
        
        except Exception:
            # If error extraction fails, continue with default values
            pass
        
        return error_info
    
    async def evaluate_expression(
        self, 
        task_instance: TaskInstance, 
        expression: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Evaluate Python expression with task context."""
        try:
            # Validate expression
            ast.parse(expression, mode='eval')
            
            # Prepare execution environment
            exec_globals = self._prepare_execution_environment(task_instance, context)
            
            # Evaluate expression
            result = eval(expression, exec_globals)
            return result
            
        except Exception as e:
            error_info = self._extract_error_info(expression, e)
            raise ScriptExecutionError(
                f"Expression evaluation failed: {str(e)}",
                line_number=error_info['line_number'],
                error_line=error_info['error_line']
            )
