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
    final result = await Navigator.push<List<String>>(
      context,
      MaterialPageRoute(
        builder: (_) => _BarcodeScannerScreen(
          title: 'Scan Tracking Numbers',
        ),
      ),
    );

    if (result != null && result.isNotEmpty && mounted) {
      setState(() {
        // Combine existing text with new scans
        final existing = _barcodeController.text.trim();
        final newBarcodes = result.join('\n');
        
        if (existing.isEmpty) {
          _barcodeController.text = newBarcodes;
        } else {
          _barcodeController.text = '$existing\n$newBarcodes';
        }
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
              maxLines: 5,
              minLines: 1,
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
  final Set<String> _scannedBarcodes = {};
  final List<String> _orderedBarcodes = [];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _addBarcode(String barcode) {
    if (!_scannedBarcodes.contains(barcode)) {
      setState(() {
        _scannedBarcodes.add(barcode);
        _orderedBarcodes.add(barcode);
      });
      
      // Provide haptic feedback
      // HapticFeedback.mediumImpact(); // Uncomment if you want haptic feedback
    }
  }

  void _removeBarcode(String barcode) {
    setState(() {
      _scannedBarcodes.remove(barcode);
      _orderedBarcodes.remove(barcode);
    });
  }

  void _clearAll() {
    setState(() {
      _scannedBarcodes.clear();
      _orderedBarcodes.clear();
    });
  }

  void _done() {
    Navigator.pop(context, _orderedBarcodes);
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
          if (_scannedBarcodes.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: _clearAll,
              tooltip: 'Clear all',
            ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: (capture) {
              final List<Barcode> barcodes = capture.barcodes;
              for (final barcode in barcodes) {
                if (barcode.rawValue != null) {
                  _addBarcode(barcode.rawValue!);
                }
              }
            },
          ),
          // Instruction overlay
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.7),
                    Colors.transparent,
                  ],
                ),
              ),
              child: Column(
                children: [
                  const Text(
                    'Scan multiple barcodes',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Point camera at barcodes to scan',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Scanned barcodes list
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(context).size.height * 0.4,
              ),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
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
                  // Handle bar
                  Container(
                    margin: const EdgeInsets.symmetric(vertical: 8),
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  // Header
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Scanned (${_scannedBarcodes.length})',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (_scannedBarcodes.isNotEmpty)
                          ElevatedButton.icon(
                            onPressed: _done,
                            icon: const Icon(Icons.check, size: 18),
                            label: const Text('Done'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primaryGreen,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            ),
                          ),
                      ],
                    ),
                  ),
                  const Divider(height: 1),
                  // List
                  if (_scannedBarcodes.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        children: [
                          Icon(
                            Icons.qr_code_scanner,
                            size: 48,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'No barcodes scanned yet',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    Flexible(
                      child: ListView.separated(
                        shrinkWrap: true,
                        padding: const EdgeInsets.only(bottom: 16),
                        itemCount: _orderedBarcodes.length,
                        separatorBuilder: (context, index) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final barcode = _orderedBarcodes[index];
                          return ListTile(
                            leading: CircleAvatar(
                              backgroundColor: AppTheme.primaryGreen.withOpacity(0.1),
                              child: Text(
                                '${index + 1}',
                                style: TextStyle(
                                  color: AppTheme.primaryGreen,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            title: Text(
                              barcode,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 14,
                              ),
                            ),
                            trailing: IconButton(
                              icon: const Icon(Icons.close, size: 20),
                              onPressed: () => _removeBarcode(barcode),
                              color: Colors.red,
                            ),
                          );
                        },
                      ),
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