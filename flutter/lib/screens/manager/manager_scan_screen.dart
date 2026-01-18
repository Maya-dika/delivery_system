import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../models/order.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';

class ManagerScanScreen extends StatefulWidget {
  const ManagerScanScreen({super.key});

  @override
  State<ManagerScanScreen> createState() => _ManagerScanScreenState();
}

class _ManagerScanScreenState extends State<ManagerScanScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _barcodeController = TextEditingController();
  final MobileScannerController _scannerController = MobileScannerController();
  bool _isConfirmingOrder = false;
  bool _isConfirmingArrival = false;
  String? _errorMessage;
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _barcodeController.addListener(() {
      setState(() {
        _hasText = _barcodeController.text.isNotEmpty;
      });
    });
  }

  @override
  void dispose() {
    _barcodeController.dispose();
    _scannerController.dispose();
    super.dispose();
  }

  Future<void> _scanBarcode() async {
    final result = await Navigator.push<String>(
      context,
      MaterialPageRoute(
        builder: (_) => _BarcodeScannerScreen(
          title: 'Scan Tracking Number',
        ),
      ),
    );

    if (result != null && mounted) {
      setState(() {
        _barcodeController.text = result;
        _errorMessage = null;
      });
    }
  }

  Future<void> _confirmOrder() async {
    final trackingNumber = _barcodeController.text.trim();
    
    if (trackingNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a tracking number')),
      );
      return;
    }

    setState(() {
      _isConfirmingOrder = true;
      _errorMessage = null;
    });

    try {
      // First fetch the order
      final order = await _apiService.getOrderByTrackingNumber(trackingNumber);
      
      if (order == null) {
        setState(() {
          _errorMessage = 'Order not found with tracking number: $trackingNumber';
          _isConfirmingOrder = false;
        });
        return;
      }

      final confirm = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Confirm Order'),
          content: Text(
            'Are you sure you want to confirm order #${order.trackingNumber}?',
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

      if (confirm != true) {
        setState(() {
          _isConfirmingOrder = false;
        });
        return;
      }

      final result = await _apiService.confirmOrdersBulk([order.id]);
      
      if (mounted) {
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                result['confirmed_orders'] != null
                    ? '${result['confirmed_orders'].length} order(s) confirmed successfully'
                    : 'Order confirmed successfully',
              ),
              backgroundColor: AppTheme.primaryGreen,
            ),
          );
          // Clear the input
          setState(() {
            _barcodeController.clear();
            _errorMessage = null;
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? 'Failed to confirm order'),
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
          _isConfirmingOrder = false;
        });
      }
    }
  }

  Future<void> _confirmArrivalWarehouse() async {
    final trackingNumber = _barcodeController.text.trim();
    
    if (trackingNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a tracking number')),
      );
      return;
    }

    setState(() {
      _isConfirmingArrival = true;
      _errorMessage = null;
    });

    try {
      // First fetch the order
      final order = await _apiService.getOrderByTrackingNumber(trackingNumber);
      
      if (order == null) {
        setState(() {
          _errorMessage = 'Order not found with tracking number: $trackingNumber';
          _isConfirmingArrival = false;
        });
        return;
      }

      final confirm = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Confirm Arrival to Warehouse'),
          content: Text(
            'Are you sure you want to confirm arrival for order #${order.trackingNumber}?',
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

      if (confirm != true) {
        setState(() {
          _isConfirmingArrival = false;
        });
        return;
      }

      final result = await _apiService.markArrivedToWarehouse([order.id]);
      
      if (mounted) {
        if (result['success'] == true) {
          final failedOrders = result['failed_orders'] as List?;
          if (failedOrders != null && failedOrders.isNotEmpty) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  'Some orders failed: ${failedOrders.length} order(s) could not be confirmed',
                ),
                backgroundColor: Colors.orange,
              ),
            );
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: const Text('Order confirmed as arrived to warehouse'),
                backgroundColor: AppTheme.primaryGreen,
              ),
            );
          }
          // Clear the input
          setState(() {
            _barcodeController.clear();
            _errorMessage = null;
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? 'Failed to confirm arrival'),
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
          _isConfirmingArrival = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Order'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Barcode Input
            TextField(
              controller: _barcodeController,
              decoration: InputDecoration(
                labelText: 'Tracking Number / Barcode',
                prefixIcon: const Icon(Icons.qr_code_scanner),
                suffixIcon: _hasText
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            _barcodeController.clear();
                            _errorMessage = null;
                          });
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              textInputAction: TextInputAction.done,
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _scanBarcode,
                icon: const Icon(Icons.qr_code_scanner, size: 18),
                label: const Text('Scan Barcode'),
                style: TextButton.styleFrom(
                  foregroundColor: AppTheme.primaryGreen,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Error Message
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
              ),

            const SizedBox(height: 24),

            // Action Buttons
            Column(
              children: [
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: (_isConfirmingOrder || _isConfirmingArrival) ? null : _confirmOrder,
                    icon: _isConfirmingOrder
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : const Icon(Icons.check_circle),
                    label: const Text('Confirm Order'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      backgroundColor: Colors.orange,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: (_isConfirmingOrder || _isConfirmingArrival) ? null : _confirmArrivalWarehouse,
                    icon: _isConfirmingArrival
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : const Icon(Icons.warehouse),
                    label: const Text('Confirm Arrival Warehouse'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      backgroundColor: AppTheme.primaryGreen,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// Barcode Scanner Screen
class _BarcodeScannerScreen extends StatefulWidget {
  final String title;

  const _BarcodeScannerScreen({
    required this.title,
  });

  @override
  State<_BarcodeScannerScreen> createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends State<_BarcodeScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();
  bool _isProcessing = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: () {
              _controller.toggleTorch();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: (capture) {
              if (_isProcessing) return;
              
              final List<Barcode> barcodes = capture.barcodes;
              if (barcodes.isNotEmpty) {
                final barcode = barcodes.first;
                if (barcode.rawValue != null) {
                  setState(() {
                    _isProcessing = true;
                  });
                  
                  // Return the scanned value
                  Navigator.pop(context, barcode.rawValue);
                }
              }
            },
          ),
          // Overlay
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
                const Text(
                  'Position barcode within the frame',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
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
        ],
      ),
    );
  }
}