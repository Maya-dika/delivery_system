import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../utils/theme.dart';

class OrderDetailScreen extends StatelessWidget {
  final Order order;

  const OrderDetailScreen({
    super.key,
    required this.order,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Order ${order.trackingNumber}'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildInfoCard(
              context,
              'Order Information',
              [
                _buildInfoRow('Tracking Number', order.trackingNumber),
                _buildInfoRow('Status', order.orderStatus),
                _buildInfoRow('Order Date', order.orderDate),
                _buildInfoRow('Order Price', order.orderPrice),
                _buildInfoRow('Delivery Fees', order.totalDeliveryFees),
              ],
            ),
            const SizedBox(height: 16),
            _buildInfoCard(
              context,
              'Supplier',
              [
                _buildInfoRow('Name', order.supplier),
                _buildInfoRow('Address', order.supplierAddress),
              ],
            ),
            const SizedBox(height: 16),
            _buildInfoCard(
              context,
              'Customer',
              [
                _buildInfoRow('Name', order.customer),
                _buildInfoRow('Address', order.customerAddress),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(
    BuildContext context,
    String title,
    List<Widget> children,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: AppTheme.lightGray,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: AppTheme.darkGray),
            ),
          ),
        ],
      ),
    );
  }
}

