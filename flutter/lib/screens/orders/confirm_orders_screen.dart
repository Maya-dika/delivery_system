import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../widgets/order_card.dart';

class ConfirmOrdersScreen extends StatefulWidget {
  const ConfirmOrdersScreen({
    super.key,
  });

  @override
  State<ConfirmOrdersScreen> createState() => _ConfirmOrdersScreenState();
}

class _ConfirmOrdersScreenState extends State<ConfirmOrdersScreen> {
  final ApiService _apiService = ApiService();
  final Set<int> _selectedOrders = {};
  bool _isConfirming = false;
  List<Order> _orders = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadOrders();
  }

  Future<void> _loadOrders() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _apiService.getOrders(length: 20);
      setState(() {
        _orders = response.data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading orders: ${e.toString()}')),
        );
      }
    }
  }

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
        title: const Text('Confirm Orders'),
        content: Text(
          'Are you sure you want to confirm ${_selectedOrders.length} order(s)?',
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
      final result = await _apiService.confirmOrdersBulk(_selectedOrders.toList());
      
      if (mounted) {
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                result['confirmed_orders'] != null
                    ? '${result['confirmed_orders'].length} orders confirmed successfully'
                    : 'Orders confirmed successfully',
              ),
              backgroundColor: AppTheme.primaryGreen,
            ),
          );
          // Refresh orders after confirmation
          await _loadOrders();
          // Clear selected orders
          setState(() {
            _selectedOrders.clear();
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? 'Failed to confirm orders'),
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
    // Filter orders that can be confirmed (draft status)
    final confirmableOrders = _orders.where((order) {
      final status = order.orderStatus.toLowerCase();
      return status == 'draft' || status.contains('pending');
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Confirm Orders (${_selectedOrders.length} selected)'),
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
              tooltip: 'Confirm Selected',
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : confirmableOrders.isEmpty
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
                        'No orders to confirm',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadOrders,
                  child: ListView.builder(
                    itemCount: confirmableOrders.length,
                    itemBuilder: (context, index) {
                      final order = confirmableOrders[index];
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
                              if (order.customer.isNotEmpty)
                                Text('Customer: ${order.customer}'),
                            ],
                          ),
                          isThreeLine: true,
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

