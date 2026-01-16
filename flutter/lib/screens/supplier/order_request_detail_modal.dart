import 'package:flutter/material.dart';
import '../../models/order_request.dart';
import '../../utils/theme.dart';

class OrderRequestDetailModal extends StatelessWidget {
  final OrderRequest orderRequest;

  const OrderRequestDetailModal({
    super.key,
    required this.orderRequest,
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

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.lightGray,
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor(orderRequest.status);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: AppTheme.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Order Request Details',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const Divider(),
          const SizedBox(height: 16),
          
          // Status Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: statusColor),
            ),
            child: Text(
              orderRequest.status.toUpperCase(),
              style: TextStyle(
                color: statusColor,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(height: 24),
          
          // Details
          _buildInfoRow(context, 'Reference:', orderRequest.reference),
          _buildInfoRow(context, 'Status:', orderRequest.status),
          _buildInfoRow(context, 'Supplier:', orderRequest.supplier.isNotEmpty ? orderRequest.supplier : 'N/A'),
          _buildInfoRow(context, 'Warehouse:', orderRequest.warehouse.isNotEmpty ? orderRequest.warehouse : 'N/A'),
          _buildInfoRow(context, 'Driver:', orderRequest.driver.isNotEmpty ? orderRequest.driver : 'Not Assigned'),
          _buildInfoRow(context, 'Orders:', orderRequest.nbOrders.toString()),
          _buildInfoRow(context, 'Packages:', orderRequest.nbPackages.toString()),
          _buildInfoRow(context, 'Created At:', orderRequest.createdAt),
          
          const SizedBox(height: 24),
          
          // Close button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryGreen,
                foregroundColor: AppTheme.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Close'),
            ),
          ),
        ],
      ),
    );
  }

  static void show(BuildContext context, OrderRequest orderRequest) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => OrderRequestDetailModal(orderRequest: orderRequest),
    );
  }
}
