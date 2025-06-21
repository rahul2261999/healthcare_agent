from verticals.retail.tools import get_orders, RetailToolsJson

retail_tools_json: RetailToolsJson = {
  "get_orders": {
    "description": "Get all the orders of the customer",
    "tool": get_orders
  }
}