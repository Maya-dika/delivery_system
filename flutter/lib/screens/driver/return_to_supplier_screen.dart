import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';

class ReturnToSupplierScreen extends StatefulWidget {
  final List<Order> orders;

  const ReturnToSupplierScreen({
    super.key,
    required this.orders,
  });

  @override
  State<ReturnToSupplierScreen> createState() => _ReturnToSupplierScreenState();
}

class _ReturnToSupplierScreenState extends State<ReturnToSupplierScreen> {
  final ApiService _apiService = ApiService();
  final Set<int> _selectedOrders = {};
  bool _isConfirming = false;

  Future<void> _returnSelected() async {
    if (_selectedOrders.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one order')),
      );
      return;
    }

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Return to Supplier'),
        content: Text(
          'Are you sure you want to return ${_selectedOrders.length} order(s) to supplier?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            child: const Text('Return'),
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
        final result = await _apiService.markReturnedToSupplier(orderId);
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
            'Returned: $successCount, Failed: $failCount',
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
    // Filter orders that can be returned (cancelled orders)
    final returnableOrders = widget.orders.where((order) {
      return order.isCancelled || 
             order.orderStatus.toLowerCase().contains('cancelled');
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Return to Supplier (${_selectedOrders.length} selected)'),
        actions: [
          if (_selectedOrders.isNotEmpty)
            IconButton(
              icon: _isConfirming
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.undo),
              onPressed: _isConfirming ? null : _returnSelected,
              tooltip: 'Return to Supplier',
            ),
        ],
      ),
      body: returnableOrders.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.undo,
                    size: 64,
                    color: AppTheme.lightGray,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No cancelled orders to return',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: returnableOrders.length,
              itemBuilder: (context, index) {
                final order = returnableOrders[index];
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



