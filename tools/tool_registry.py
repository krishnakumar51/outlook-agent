#!/usr/bin/env python3
"""
Tool Registry - Central registration and management of all mobile automation tools
Provides unified interface for tool creation and management
"""

from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool

from tools.mobile_ui_tool import create_mobile_ui_tool
from tools.gestures_tool import create_gestures_tool
from tools.ocr_tool import create_ocr_tool
from tools.navigator_tool import create_navigator_tool

class ToolRegistry:
    """Registry for managing mobile automation tools."""

    def __init__(self):
        self.tools = {}
        self.driver = None

    def initialize_with_driver(self, driver) -> List[BaseTool]:
        """Initialize all tools with the Appium driver."""
        self.driver = driver

        print("🔧 [TOOLS] Initializing tool registry with Appium driver...")

        try:
            # Create all tool instances
            self.tools = {
                "mobile_ui": create_mobile_ui_tool(driver),
                "gestures": create_gestures_tool(driver), 
                "ocr": create_ocr_tool(driver),
                "navigator": create_navigator_tool(driver)
            }

            tool_names = list(self.tools.keys())
            print(f"✅ [TOOLS] Registered tools: {tool_names}")

            return list(self.tools.values())

        except Exception as e:
            print(f"❌ [TOOLS] Error initializing tools: {e}")
            return []

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self.tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self.tools.values())

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all tools."""
        return {name: tool.description for name, tool in self.tools.items()}

    def print_tool_summary(self):
        """Print summary of available tools."""
        print("🛠️ [TOOLS] Available Tools Summary:")
        print("=" * 50)

        for name, tool in self.tools.items():
            print(f"📱 {name.upper()}")
            # Extract first line of description
            desc_lines = tool.description.strip().split('\n')
            short_desc = desc_lines[0] if desc_lines else "No description"
            print(f"   {short_desc}")

            # Show available actions from description
            if "Available" in tool.description:
                actions_section = tool.description.split("Available")[1].split("actions:")[1] if "actions:" in tool.description else ""
                if actions_section:
                    actions = [line.strip().split(':')[0].replace('-', '').strip() 
                             for line in actions_section.split('\n') if line.strip().startswith('-')]
                    if actions:
                        print(f"   Actions: {', '.join(actions[:5])}")
            print()

# Global registry instance
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry

def create_tool_list(driver) -> List[BaseTool]:
    """
    Convenience function to create and return all tools for a driver.
    This is the main entry point for getting tools for LangGraph ToolNode.
    """
    registry = get_tool_registry()
    tools = registry.initialize_with_driver(driver)

    # Print tool summary for visibility
    if tools:
        registry.print_tool_summary()

    return tools

def get_tool_descriptions_for_prompt() -> str:
    """
    Get formatted tool descriptions for LLM prompt.
    Returns a string describing all available tools and their capabilities.
    """
    registry = get_tool_registry()

    if not registry.tools:
        return "No tools available. Initialize registry with driver first."

    descriptions = []
    descriptions.append("Available Mobile Automation Tools:")
    descriptions.append("=" * 40)

    for name, tool in registry.tools.items():
        descriptions.append(f"\n🔧 {name.upper()}")
        descriptions.append(f"Purpose: {tool.description.split('.')[0]}.")

        # Extract actions if available
        if "Available" in tool.description and "actions:" in tool.description:
            actions_part = tool.description.split("Available")[1].split("actions:")[1]
            actions = []
            for line in actions_part.split('\n'):
                if line.strip().startswith('-'):
                    action_desc = line.strip()[1:].strip()
                    if ':' in action_desc:
                        action_name = action_desc.split(':')[0].strip()
                        actions.append(action_name)

            if actions:
                descriptions.append(f"Actions: {', '.join(actions)}")

    descriptions.append("\n" + "=" * 40)
    descriptions.append("Use tools by calling them with appropriate action and parameters.")
    descriptions.append("Always check OCR first if you need to understand screen content.")
    descriptions.append("Prefer exists/wait_for before attempting click/type operations.")

    return "\n".join(descriptions)
