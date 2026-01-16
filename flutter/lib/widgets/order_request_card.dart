import 'package:flutter/material.dart';
import '../models/order_request.dart';
import '../utils/theme.dart';

class OrderRequestCard extends StatelessWidget {
  final OrderRequest orderRequest;
  final VoidCallback? onTap;

  const OrderRequestCard({
    super.key,
    required this.orderRequest,
    this.onTap,
  });

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'requested':
        return Colors.orange;
      case 'confirmed':
        return AppTheme.primaryGreen;
      case 'picked_up':
        return Colors.blue;
      case 'cancelled':
        return Colors.red;
      default:
        return AppTheme.darkGray;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'requested':
        return Icons.pending;
      case 'confirmed':
        return Icons.check_circle;
      case 'picked_up':
        return Icons.local_shipping;
      case 'cancelled':
        return Icons.cancel;
      default:
        return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor(orderRequest.status);
    final statusIcon = _getStatusIcon(orderRequest.status);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Circular icon with status indicator
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: statusColor, width: 2),
                ),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Icon(
                      Icons.description,
                      color: statusColor,
                      size: 32,
                    ),
                    // Status icon in bottom right
                    Positioned(
                      bottom: 4,
                      right: 4,
                      child: Container(
                        width: 16,
                        height: 16,
                        decoration: BoxDecoration(
                          color: statusColor,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          statusIcon,
                          color: AppTheme.white,
                          size: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              // Order request details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Ref: ${orderRequest.reference}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      orderRequest.status,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: statusColor,
                            fontWeight: FontWeight.w500,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.inventory_2,
                          size: 14,
                          color: AppTheme.lightGray,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${orderRequest.nbOrders} orders, ${orderRequest.nbPackages} packages',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppTheme.lightGray,
                              ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // Arrow icon
              Icon(
                Icons.chevron_right,
                color: AppTheme.lightGray,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
