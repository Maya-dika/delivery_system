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
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Full Screen Camera Scanner - scans entire screen
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

          // Top bar with controls
          SafeArea(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.7),
                    Colors.black.withOpacity(0.3),
                    Colors.transparent,
                  ],
                ),
              ),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white, size: 28),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const Expanded(
                    child: Text(
                      'Scan & Action',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.flash_on, color: Colors.white, size: 28),
                    onPressed: () {
                      _scannerController.toggleTorch();
                    },
                  ),
                ],
              ),
            ),
          ),

          // Center guide (visual only - not restricting scan area)
      //  Center(
      //     child: Container(
      //       width: MediaQuery.of(context).size.width * 0.8,  // 80% of screen width
      //       height: MediaQuery.of(context).size.height * 0.8, // half screen height
      //       decoration: BoxDecoration(
      //         border: Border.all(
      //           color: AppTheme.primaryGreen,
      //           width: 4,
      //         ),
      //         borderRadius: BorderRadius.circular(20),
      //       ),
      //     ),
      //   ),

          // Bottom instruction text
          Positioned(
            bottom: 120,
            left: 0,
            right: 0,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: const Text(
                    'Scan barcode anywhere on screen',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
                if (_isProcessing) ...[
                  const SizedBox(height: 16),
                  const CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      'Processing...',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
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
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, -5),
                    ),
                  ],
                ),
                child: SafeArea(
                  top: false,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Drag handle
                      Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      if (_errorMessage != null)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.red.shade200, width: 2),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.error_outline, color: Colors.red.shade700, size: 32),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: TextStyle(
                                    color: Colors.red.shade700,
                                    fontSize: 15,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        )
                      else if (_scannedOrder != null)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryGreen.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.primaryGreen, width: 2),
                          ),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: const BoxDecoration(
                                  color: AppTheme.primaryGreen,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.check,
                                  color: Colors.white,
                                  size: 24,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'Order Found',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.darkGray,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      _scannedOrder!.trackingNumber,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 18,
                                        color: AppTheme.primaryGreen,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: Colors.grey[200],
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        _scannedOrder!.orderStatus,
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey[700],
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: _resetScan,
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                side: BorderSide(color: AppTheme.darkGray, width: 2),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: const Text(
                                'Scan Again',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
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
                                  padding: const EdgeInsets.symmetric(vertical: 16),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  elevation: 0,
                                ),
                                child: const Text(
                                  'View Action',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
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