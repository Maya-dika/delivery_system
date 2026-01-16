import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../widgets/order_card.dart';

class ConfirmPickupScreen extends StatefulWidget {
  final List<Order> orders;

  const ConfirmPickupScreen({
    super.key,
    required this.orders,
  });

  @override
  State<ConfirmPickupScreen> createState() => _ConfirmPickupScreenState();
}

class _ConfirmPickupScreenState extends State<ConfirmPickupScreen> {
  final ApiService _apiService = ApiService();
  final Set<int> _selectedOrders = {};
  bool _isConfirming = false;

  Future<void> _confirmSelected() async {
    if (_selectedOrders.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one order')),
      );
      return;
    }

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Pickup'),
        content: Text(
          'Are you sure you want to confirm pickup for ${_selectedOrders.length} order(s)?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() {
      _isConfirming = true;
    });

    int successCount = 0;
    int failCount = 0;

    for (final orderId in _selectedOrders) {
      try {
        final result = await _apiService.confirmPickup(orderId);
        if (result['success'] == true) {
          successCount++;
        } else {
          failCount++;
        }
      } catch (e) {
        failCount++;
      }
    }

    if (mounted) {
      setState(() {
        _isConfirming = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Confirmed: $successCount, Failed: $failCount',
          ),
          backgroundColor: failCount > 0 ? Colors.orange : AppTheme.primaryGreen,
        ),
      );

      if (successCount > 0) {
        Navigator.pop(context, true); // Return true to refresh
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Filter orders that can be confirmed for pickup
    final pickupOrders = widget.orders.where((order) {
      final status = order.orderStatus.toLowerCase();
      return status == 'confirmed' || status.contains('pending_pickup');
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Confirm Pickup (${_selectedOrders.length} selected)'),
        actions: [
          if (_selectedOrders.isNotEmpty)
            IconButton(
              icon: _isConfirming
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.check_circle),
              onPressed: _isConfirming ? null : _confirmSelected,
              tooltip: 'Confirm Pickup',
            ),
        ],
      ),
      body: pickupOrders.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.check_circle_outline,
                    size: 64,
                    color: AppTheme.lightGray,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No orders ready for pickup confirmation',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: pickupOrders.length,
              itemBuilder: (context, index) {
                final order = pickupOrders[index];
                final isSelected = _selectedOrders.contains(order.id);

                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: CheckboxListTile(
                    value: isSelected,
                    onChanged: (value) {
                      setState(() {
                        if (value == true) {
                          _selectedOrders.add(order.id);
                        } else {
                          _selectedOrders.remove(order.id);
                        }
                      });
                    },
                    title: Text(
                      'Order #${order.trackingNumber}',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text('Status: ${order.orderStatus}'),
                        if (order.supplier.isNotEmpty)
                          Text('Supplier: ${order.supplier}'),
                      ],
                    ),
                    isThreeLine: true,
                  ),
                );
              },
            ),
    );
  }
}



