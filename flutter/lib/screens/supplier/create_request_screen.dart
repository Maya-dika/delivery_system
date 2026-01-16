import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/warehouse.dart';
import '../../models/delivery_pricelist.dart';
import '../../models/api_response.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';

class CreateRequestScreen extends StatefulWidget {
  final User user;

  const CreateRequestScreen({
    super.key,
    required this.user,
  });

  @override
  State<CreateRequestScreen> createState() => _CreateRequestScreenState();
}

class _CreateRequestScreenState extends State<CreateRequestScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _apiService = ApiService();
  
  // Form controllers
  Warehouse? _selectedWarehouse;
  DeliveryPriceList? _selectedPricelist;
  final TextEditingController _nbOrdersController = TextEditingController();
  final TextEditingController _nbPackagesController = TextEditingController();
  final TextEditingController _totalAmountController = TextEditingController();

  // Data lists
  List<Warehouse> _warehouses = [];
  List<DeliveryPriceList> _pricelists = [];
  
  // Loading states
  bool _isLoadingWarehouses = false;
  bool _isLoadingPricelists = false;
  bool _isLoadingDefaults = false;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _nbOrdersController.dispose();
    _nbPackagesController.dispose();
    _totalAmountController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoadingWarehouses = true;
      _isLoadingPricelists = true;
      _isLoadingDefaults = true;
    });

    try {
      // Load warehouses and pricelists in parallel
      // Try to get defaults, but don't fail if it doesn't work
      SupplierDefaultsResponse? defaults;
      print(widget.user.supplierId);
      if (widget.user.supplierId != null) {
        try {
          defaults = await _apiService.getSupplierDefaults(supplierId: widget.user.supplierId);
        } catch (e) {
          // If defaults fail, continue without them
          defaults = null;
        }
      }

      final results = await Future.wait([
        _apiService.getWarehouses(length: 100),
        _apiService.getDeliveryPriceLists(length: 100),
      ]);

      final warehousesResponse = results[0] as WarehouseApiResponse;
      final pricelistsResponse = results[1] as DeliveryPriceListApiResponse;

      setState(() {
        _warehouses = warehousesResponse.data;
        _pricelists = pricelistsResponse.data;
        _isLoadingWarehouses = false;
        _isLoadingPricelists = false;
        _isLoadingDefaults = false;

        // Set defaults if available
        if (defaults != null && defaults.warehouseId != null) {
          try {
            _selectedWarehouse = _warehouses.firstWhere(
              (w) => w.id == defaults!.warehouseId,
            );
          } catch (e) {
            // Default warehouse not found in list, select first if available
            if (_warehouses.isNotEmpty) {
              _selectedWarehouse = _warehouses.first;
            }
          }
        } else if (_warehouses.isNotEmpty) {
          // Select first warehouse if no default
          _selectedWarehouse = _warehouses.first;
        }

        if (defaults != null && defaults.pricelistId != null) {
          try {
            _selectedPricelist = _pricelists.firstWhere(
              (p) => p.id == defaults!.pricelistId,
            );
          } catch (e) {
            // Default pricelist not found, try to select default or first
            if (_pricelists.isNotEmpty) {
              try {
                _selectedPricelist = _pricelists.firstWhere(
                  (p) => p.defaultList,
                );
              } catch (e) {
                _selectedPricelist = _pricelists.first;
              }
            }
          }
        } else if (_pricelists.isNotEmpty) {
          // Select default pricelist if available, otherwise first
          try {
            _selectedPricelist = _pricelists.firstWhere(
              (p) => p.defaultList,
            );
          } catch (e) {
            _selectedPricelist = _pricelists.first;
          }
        }
      });
    } catch (e) {
      setState(() {
        _isLoadingWarehouses = false;
        _isLoadingPricelists = false;
        _isLoadingDefaults = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading data: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_selectedWarehouse == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a warehouse'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    try {
      final nbOrders = int.parse(_nbOrdersController.text);
      final nbPackages = int.parse(_nbPackagesController.text);
      final totalAmount = double.parse(_totalAmountController.text);
      print(widget.user.supplierId);
      final result = await _apiService.createOrderRequest(
        warehouse: _selectedWarehouse!.id,
        supplier: widget.user.supplierId ?? 0,
        nbOrders: nbOrders,
        nbPackages: nbPackages,
        totalAmount: totalAmount,
        deliveryPricelist: _selectedPricelist?.id,
      );

      if (mounted) {
        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['message'] ?? 'Order request created successfully'),
              backgroundColor: AppTheme.primaryGreen,
            ),
          );
          Navigator.pop(context, true); // Return true to refresh
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['error'] ?? 'Failed to create order request'),
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
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Order Request'),
      ),
      body: (_isLoadingWarehouses || _isLoadingPricelists || _isLoadingDefaults)
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Warehouse Dropdown
                    DropdownButtonFormField<Warehouse>(
                      value: _selectedWarehouse,
                      decoration: const InputDecoration(
                        labelText: 'Warehouse *',
                        prefixIcon: Icon(Icons.warehouse),
                      ),
                      items: _warehouses.map((warehouse) {
                        return DropdownMenuItem<Warehouse>(
                          value: warehouse,
                          child: Text(warehouse.name),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() {
                          _selectedWarehouse = value;
                        });
                      },
                      validator: (value) {
                        if (value == null) {
                          return 'Please select a warehouse';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Number of Orders
                    TextFormField(
                      controller: _nbOrdersController,
                      decoration: const InputDecoration(
                        labelText: 'Number of Orders *',
                        prefixIcon: Icon(Icons.numbers),
                      ),
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter number of orders';
                        }
                        final num = int.tryParse(value);
                        if (num == null || num <= 0) {
                          return 'Please enter a valid number greater than 0';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Number of Packages
                    TextFormField(
                      controller: _nbPackagesController,
                      decoration: const InputDecoration(
                        labelText: 'Number of Packages *',
                        prefixIcon: Icon(Icons.inventory_2),
                      ),
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter number of packages';
                        }
                        final num = int.tryParse(value);
                        if (num == null || num <= 0) {
                          return 'Please enter a valid number greater than 0';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Total Amount
                    TextFormField(
                      controller: _totalAmountController,
                      decoration: const InputDecoration(
                        labelText: 'Total Amount *',
                        prefixIcon: Icon(Icons.attach_money),
                      ),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
                      ],
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter total amount';
                        }
                        final num = double.tryParse(value);
                        if (num == null || num <= 0) {
                          return 'Please enter a valid amount greater than 0';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Delivery Price List Dropdown
                    DropdownButtonFormField<DeliveryPriceList>(
                      value: _selectedPricelist,
                      decoration: const InputDecoration(
                        labelText: 'Delivery Price List',
                        prefixIcon: Icon(Icons.list_alt),
                        helperText: 'Optional',
                      ),
                      items: _pricelists.map((pricelist) {
                        return DropdownMenuItem<DeliveryPriceList>(
                          value: pricelist,
                          child: Row(
                            children: [
                              Text(pricelist.name),
                              if (pricelist.defaultList) ...[
                                const SizedBox(width: 8),
                                const Text(
                                  '(Default)',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() {
                          _selectedPricelist = value;
                        });
                      },
                    ),
                    const SizedBox(height: 32),

                    // Submit Button
                    ElevatedButton(
                      onPressed: _isSubmitting ? null : _handleSubmit,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryGreen,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: _isSubmitting
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : const Text('Create Request'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
