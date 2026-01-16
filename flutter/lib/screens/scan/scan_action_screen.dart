import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../models/order.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../driver/confirm_pickup_screen.dart';
import '../driver/mark_delivered_screen.dart';
import '../driver/return_to_supplier_screen.dart';
import '../orders/confirm_orders_screen.dart';
import '../orders/order_detail_screen.dart';

class ScanActionScreen extends StatefulWidget {
  final User user;

  const ScanActionScreen({
    super.key,
    required this.user,
  });

  @override
  State<ScanActionScreen> createState() => _ScanActionScreenState();
}

class _ScanActionScreenState extends State<ScanActionScreen> {
  final ApiService _apiService = ApiService();
  final MobileScannerController _scannerController = MobileScannerController();
  
  bool _isProcessing = false;
  String? _lastScannedCode;
  Order? _scannedOrder;
  String? _errorMessage;
  bool _showResult = false;

  @override
  void dispose() {
    _scannerController.dispose();
    super.dispose();
  }

  Future<void> _processBarcode(String code) async {
    // Prevent duplicate processing
    if (_isProcessing || _lastScannedCode == code) {
      return;
    }

    setState(() {
      _isProcessing = true;
      _lastScannedCode = code;
      _errorMessage = null;
      _scannedOrder = null;
      _showResult = false;
    });

    try {
      // Fetch order by tracking number
      final order = await _apiService.getOrderByTrackingNumber(code);
      
      if (order == null) {
        setState(() {
          _errorMessage = 'Order not found with tracking number: $code';
          _isProcessing = false;
          _showResult = true;
        });
        return;
      }

      setState(() {
        _scannedOrder = order;
        _isProcessing = false;
        _showResult = true;
      });

      // Automatically show action dialog
      _showActionDialog(order);
    } catch (e) {
      setState(() {
        _errorMessage = 'Error: ${e.toString()}';
        _isProcessing = false;
        _showResult = true;
      });
    }
  }

  void _showActionDialog(Order order) {
    final action = _determineNextAction(order);
    
    if (action == null) {
      // No action available, just show order details
      _showOrderDetails(order);
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(action.title),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Order: ${order.trackingNumber}'),
            const SizedBox(height: 8),
            Text('Status: ${order.orderStatus}'),
            const SizedBox(height: 16),
            Text(action.description),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _showOrderDetails(order);
            },
            child: const Text('View Details'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _executeAction(action, order);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryGreen,
            ),
            child: Text(action.buttonText),
          ),
        ],
      ),
    );
  }

  void _showOrderDetails(Order order) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => OrderDetailScreen(order: order),
      ),
    );
  }

  void _executeAction(ScanAction action, Order order) {
    switch (action.type) {
      case ScanActionType.confirmPickup:
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ConfirmPickupScreen(orders: [order]),
          ),
        ).then((refreshed) {
          if (refreshed == true) {
            _resetScan();
          }
        });
        break;
      
      case ScanActionType.markDelivered:
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => MarkDeliveredScreen(orders: [order]),
          ),
        ).then((refreshed) {
          if (refreshed == true) {
            _resetScan();
          }
        });
        break;
      
      case ScanActionType.returnToSupplier:
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ReturnToSupplierScreen(orders: [order]),
          ),
        ).then((refreshed) {
          if (refreshed == true) {
            _resetScan();
          }
        });
        break;
      
      case ScanActionType.confirmOrder:
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => const ConfirmOrdersScreen(),
          ),
        ).then((refreshed) {
          if (refreshed == true) {
            _resetScan();
          }
        });
        break;
      
      case ScanActionType.assignDriver:
        // For now, show order details - assign driver functionality can be added later
        _showOrderDetails(order);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Driver assignment feature coming soon'),
          ),
        );
        break;
      
      case ScanActionType.viewDetails:
        _showOrderDetails(order);
        break;
    }
  }

  ScanAction? _determineNextAction(Order order) {
    final status = order.orderStatus.toLowerCase();
    final isDriver = widget.user.isDriver;
    final isManager = widget.user.isManager;

    if (isDriver) {
      // Driver actions
      if (status == 'confirmed' || status.contains('pending_pickup')) {
        return ScanAction(
          type: ScanActionType.confirmPickup,
          title: 'Confirm Pickup',
          description: 'This order is ready for pickup confirmation.',
          buttonText: 'Confirm Pickup',
        );
      }
      
      if (status.contains('out_for_delivery') || status.contains('in_warehouse')) {
        return ScanAction(
          type: ScanActionType.markDelivered,
          title: 'Mark as Delivered',
          description: 'This order can be marked as delivered.',
          buttonText: 'Mark Delivered',
        );
      }
      
      if (status.contains('return') || order.isCancelled) {
        return ScanAction(
          type: ScanActionType.returnToSupplier,
          title: 'Return to Supplier',
          description: 'This order needs to be returned to the supplier.',
          buttonText: 'Return to Supplier',
        );
      }
    }

    if (isManager) {
      // Manager actions
      if (status == 'draft') {
        return ScanAction(
          type: ScanActionType.confirmOrder,
          title: 'Confirm Order',
          description: 'This order needs to be confirmed.',
          buttonText: 'Confirm Order',
        );
      }
      
      if (status == 'confirmed') {
        return ScanAction(
          type: ScanActionType.assignDriver,
          title: 'Assign Driver',
          description: 'This order needs a driver assignment.',
          buttonText: 'Assign Driver',
        );
      }
    }

    // Default: show order details
    return ScanAction(
      type: ScanActionType.viewDetails,
      title: 'Order Details',
      description: 'View order information.',
      buttonText: 'View Details',
    );
  }

  void _resetScan() {
    setState(() {
      _lastScannedCode = null;
      _scannedOrder = null;
      _errorMessage = null;
      _showResult = false;
      _isProcessing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan & Action'),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: () {
              _scannerController.toggleTorch();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // Camera Scanner
          MobileScanner(
            controller: _scannerController,
            onDetect: (capture) {
              final List<Barcode> barcodes = capture.barcodes;
              if (barcodes.isNotEmpty) {
                final barcode = barcodes.first;
                if (barcode.rawValue != null) {
                  _processBarcode(barcode.rawValue!);
                }
              }
            },
          ),

          // Overlay with scanning area
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.black.withOpacity(0.5),
                  Colors.transparent,
                  Colors.transparent,
                  Colors.transparent,
                  Colors.transparent,
                  Colors.black.withOpacity(0.5),
                ],
                stops: const [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
              ),
            ),
            child: Column(
              children: [
                const Spacer(),
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 40),
                  height: 250,
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: AppTheme.primaryGreen,
                      width: 3,
                    ),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Stack(
                    children: [
                      // Corner indicators
                      Positioned(
                        top: 0,
                        left: 0,
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            border: Border(
                              top: BorderSide(color: AppTheme.primaryGreen, width: 4),
                              left: BorderSide(color: AppTheme.primaryGreen, width: 4),
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        top: 0,
                        right: 0,
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            border: Border(
                              top: BorderSide(color: AppTheme.primaryGreen, width: 4),
                              right: BorderSide(color: AppTheme.primaryGreen, width: 4),
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        left: 0,
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(color: AppTheme.primaryGreen, width: 4),
                              left: BorderSide(color: AppTheme.primaryGreen, width: 4),
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(color: AppTheme.primaryGreen, width: 4),
                              right: BorderSide(color: AppTheme.primaryGreen, width: 4),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'Position barcode within the frame',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 8),
                if (_isProcessing)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
                    ),
                  ),
                const Spacer(),
              ],
            ),
          ),

          // Result overlay
          if (_showResult)
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.2),
                      blurRadius: 10,
                      offset: const Offset(0, -2),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_errorMessage != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline, color: Colors.red.shade700),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                _errorMessage!,
                                style: TextStyle(color: Colors.red.shade700),
                              ),
                            ),
                          ],
                        ),
                      )
                    else if (_scannedOrder != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryGreen.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppTheme.primaryGreen),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.check_circle, color: AppTheme.primaryGreen),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Order Found: ${_scannedOrder!.trackingNumber}',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: AppTheme.primaryGreen,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Status: ${_scannedOrder!.orderStatus}',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: _resetScan,
                            child: const Text('Scan Again'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        if (_scannedOrder != null)
                          Expanded(
                            child: ElevatedButton(
                              onPressed: () {
                                _showActionDialog(_scannedOrder!);
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.primaryGreen,
                              ),
                              child: const Text('View Action'),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

enum ScanActionType {
  confirmPickup,
  markDelivered,
  returnToSupplier,
  confirmOrder,
  assignDriver,
  viewDetails,
}

class ScanAction {
  final ScanActionType type;
  final String title;
  final String description;
  final String buttonText;

  ScanAction({
    required this.type,
    required this.title,
    required this.description,
    required this.buttonText,
  });
}

