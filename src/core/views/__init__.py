"""
Vues de l'application core — réexportées depuis les sous-modules.
"""
from .dashboard import (  # noqa: F401
    create_order_ajax,
    dashboard,
    extend_contract_ajax,
    update_inventory_ajax,
)
from .exports import (  # noqa: F401
    export_inventories,
    export_inventory,
    export_items,
    export_monthly_stats,
    export_order,
    export_orders,
)
from .inventory import change_inventory, print_inventory_sheet  # noqa: F401
from .management import (  # noqa: F401
    help_view,
    staff_management,
    suppliers_management,
    supplies_management,
)
