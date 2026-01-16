import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';

class MarkDeliveredScreen extends StatefulWidget {
  final List<Order> orders;

  const MarkDeliveredScreen({
    super.key,
    required this.orders,
  });

  @override
  State<MarkDeliveredScreen> createState() => _MarkDeliveredScreenState();
}

class _MarkDeliveredScreenState extends State<MarkDeliveredScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _verificationCodeController = TextEditingController();
  final Set<int> _selectedOrders = {};
  bool _isConfirming = false;

  @override
  void dispose() {
    _verificationCodeController.dispose();
    super.dispose();
  }

  Future<void> _markAsDelivered() async {
    if (_selectedOrders.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one order')),
      );
      return;
    }

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Mark as Delivered'),
        content: Text(
          'Are you sure you want to mark ${_selectedOrders.length} order(s) as delivered?',
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

    try {
      final verificationCode = _verificationCodeController.text.trim();
      final result = await _apiService.markAsDelivered(
        _selectedOrders.toList(),
        verificationCode: verificationCode.isEmpty ? null : verificationCode,
      );

      if (mounted) {
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                result['updated_orders'] != null
                    ? '${result['updated_orders'].length} orders marked as delivered'
                    : 'Orders marked as delivered successfully',
              ),
              backgroundColor: AppTheme.primaryGreen,
            ),
          );
          Navigator.pop(context, true); // Return true to refresh
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? 'Failed to mark orders as delivered'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isConfirming = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Filter orders that can be marked as delivered
    final deliverableOrders = widget.orders.where((order) {
      final status = order.orderStatus.toLowerCase();
      return status.contains('out_for_delivery') || status.contains('in_warehouse');
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Mark as Delivered (${_selectedOrders.length} selected)'),
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
              onPressed: _isConfirming ? null : _markAsDelivered,
              tooltip: 'Mark as Delivered',
            ),
        ],
      ),
      body: Column(
        children: [
          // Verification Code Input
          if (_selectedOrders.length == 1)
            Card(
              margin: const EdgeInsets.all(16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: TextField(
                  controller: _verificationCodeController,
                  decoration: const InputDecoration(
                    labelText: 'Verification Code (Optional)',
                    hintText: 'Enter verification code if required',
                    prefixIcon: Icon(Icons.lock),
                  ),
                ),
              ),
            ),
          
          // Orders List
          Expanded(
            child: deliverableOrders.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.local_shipping,
                          size: 64,
                          color: AppTheme.lightGray,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'No orders ready for delivery',
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: deliverableOrders.length,
                    itemBuilder: (context, index) {
                      final order = deliverableOrders[index];
                      final isSelected = _selectedOrders.contains(order.id);

                      return Card(
                        margin: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
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
                              if (order.customer.isNotEmpty)
                                Text('Customer: ${order.customer}'),
                              if (order.customerAddress.isNotEmpty)
                                Text('Address: ${order.customerAddress}'),
                            ],
                          ),
                          isThreeLine: true,
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}



