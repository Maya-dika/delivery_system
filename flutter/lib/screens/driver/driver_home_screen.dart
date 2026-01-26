import 'package:flutter/material.dart';
import '../../models/order.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../widgets/order_card.dart';
import '../../widgets/quick_action_button.dart';
import '../orders/order_detail_screen.dart';
import '../profile/profile_screen.dart';
import '../scan/scan_action_screen.dart';
import '../pickup/pickup_screen.dart';
import '../dropoff/dropoff_screen.dart';
import '../promo/promo_screen.dart';
import '../topup/topup_screen.dart';
import 'driver_statement_screen.dart';
import 'driver_performance_screen.dart';

class DriverHomeScreen extends StatefulWidget {
  final User user;

  const DriverHomeScreen({
    super.key,
    required this.user,
  });

  @override
  State<DriverHomeScreen> createState() => _DriverHomeScreenState();
}

class _DriverHomeScreenState extends State<DriverHomeScreen> {
  final ApiService _apiService = ApiService();
  List<Order> _orders = [];
  bool _isLoading = true;
  int _currentNavIndex = 0;
  
  // Task-related state
  List<Order> _pickupOrders = [];
  List<Order> _deliveryOrders = [];
  bool _isLoadingPickup = false;
  bool _isLoadingDelivery = false;
  String? _selectedPickupStatus;
  String? _selectedDeliveryStatus;
  bool _pickupLoaded = false;
  bool _deliveryLoaded = false;

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
      final response = await _apiService.getOrders(length: 50);
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

  Future<void> _loadPickupOrders({String? status}) async {
    setState(() {
      _isLoadingPickup = true;
    });

    try {
      final response = await _apiService.getOrders(
        length: 50,
        status: status,
      );
      setState(() {
        _pickupOrders = response.data;
        _isLoadingPickup = false;
        _selectedPickupStatus = status;
        _pickupLoaded = true;
      });
    } catch (e) {
      setState(() {
        _isLoadingPickup = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading pickup orders: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _loadDeliveryOrders({String? status}) async {
    setState(() {
      _isLoadingDelivery = true;
    });

    try {
      final response = await _apiService.getOrders(
        length: 50,
        status: status,
      );
      setState(() {
        _deliveryOrders = response.data;
        _isLoadingDelivery = false;
        _selectedDeliveryStatus = status;
        _deliveryLoaded = true;
      });
    } catch (e) {
      setState(() {
        _isLoadingDelivery = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading delivery orders: ${e.toString()}')),
        );
      }
    }
  }

  void _onNavTap(int index) {
    // Load data for tabs that haven't been loaded yet
    if (index == 1 && !_pickupLoaded) {
      _loadPickupOrders(status: null);
    } else if (index == 2 && !_deliveryLoaded) {
      _loadDeliveryOrders(status: null);
    }

    setState(() {
      _currentNavIndex = index;
    });
  }

  Widget _buildHomeTab() {
    final assignedOrders = _orders;
    
    return RefreshIndicator(
      onRefresh: _loadOrders,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Driver Stats Cards
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: _buildStatCard(
                      context,
                      'Total Orders',
                      assignedOrders.length.toString(),
                      Icons.local_shipping,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      context,
                      'Pending',
                      assignedOrders
                          .where((o) => o.orderStatus
                              .toLowerCase()
                              .contains('pending'))
                          .length
                          .toString(),
                      Icons.pending,
                      color: Colors.orange,
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Expanded(
                    child: _buildStatCard(
                      context,
                      'Delivered',
                      assignedOrders
                          .where((o) => o.orderStatus
                              .toLowerCase()
                              .contains('delivered'))
                          .length
                          .toString(),
                      Icons.check_circle,
                      color: AppTheme.primaryGreen,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      context,
                      'In Transit',
                      assignedOrders
                          .where((o) => o.orderStatus
                              .toLowerCase()
                              .contains('transit'))
                          .length
                          .toString(),
                      Icons.directions_car,
                      color: Colors.blue,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Quick Actions Section
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Quick Actions',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      // QuickActionButton(
                      //   icon: Icons.qr_code_scanner,
                      //   label: 'Scan',
                      //   onTap: () {
                      //     Navigator.push(
                      //       context,
                      //       MaterialPageRoute(
                      //         builder: (_) => ScanActionScreen(user: widget.user),
                      //       ),
                      //     );
                      //   },
                      // ),
                      QuickActionButton(
                        icon: Icons.local_shipping,
                        label: 'Pick Up',
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const PickUpScreen(),
                            ),
                          );
                        },
                      ),
                      QuickActionButton(
                        icon: Icons.delivery_dining,
                        label: 'Drop Off',
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const DropOffScreen(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Assigned Orders Section
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'My Assigned Orders (${assignedOrders.length})',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            const SizedBox(height: 16),
            
            // Orders List
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (assignedOrders.isEmpty)
              Padding(
                padding: const EdgeInsets.all(32),
                child: Center(
                  child: Text(
                    'No assigned orders',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
              )
            else
              ...assignedOrders.map((order) => OrderCard(
                    order: order,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => OrderDetailScreen(order: order),
                        ),
                      );
                    },
                  )),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildPickupTab() {
    return RefreshIndicator(
      onRefresh: () => _loadPickupOrders(status: _selectedPickupStatus),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Filter Section
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'All',
                      _selectedPickupStatus == null,
                      () => _loadPickupOrders(status: null),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'Assigned',
                      _selectedPickupStatus == 'assigned',
                      () => _loadPickupOrders(status: 'assigned'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'Pending',
                      _selectedPickupStatus == 'pending',
                      () => _loadPickupOrders(status: 'pending'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            
            // Pickup Orders List
            if (_isLoadingPickup)
              const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_pickupOrders.isEmpty)
              Padding(
                padding: const EdgeInsets.all(32),
                child: Center(
                  child: Column(
                    children: [
                      Icon(
                        Icons.local_shipping_outlined,
                        size: 64,
                        color: AppTheme.lightGray,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'No pickup orders',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ],
                  ),
                ),
              )
            else
              ..._pickupOrders.map((order) => OrderCard(
                    order: order,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => OrderDetailScreen(order: order),
                        ),
                      );
                    },
                  )),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildDeliveryTab() {
    return RefreshIndicator(
      onRefresh: () => _loadDeliveryOrders(status: _selectedDeliveryStatus),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Filter Section
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'All',
                      _selectedDeliveryStatus == null,
                      () => _loadDeliveryOrders(status: null),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'In Transit',
                      _selectedDeliveryStatus == 'in_transit',
                      () => _loadDeliveryOrders(status: 'in_transit'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildFilterChip(
                      context,
                      'Delivered',
                      _selectedDeliveryStatus == 'delivered',
                      () => _loadDeliveryOrders(status: 'delivered'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            
            // Delivery Orders List
            if (_isLoadingDelivery)
              const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_deliveryOrders.isEmpty)
              Padding(
                padding: const EdgeInsets.all(32),
                child: Center(
                  child: Column(
                    children: [
                      Icon(
                        Icons.delivery_dining_outlined,
                        size: 64,
                        color: AppTheme.lightGray,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'No delivery orders',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ],
                  ),
                ),
              )
            else
              ..._deliveryOrders.map((order) => OrderCard(
                    order: order,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => OrderDetailScreen(order: order),
                        ),
                      );
                    },
                  )),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildPerformanceTab() {
    return DriverPerformanceScreen(user: widget.user);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        elevation: 4,
        shadowColor: Colors.black.withOpacity(0.1),
        backgroundColor: AppTheme.white,
        surfaceTintColor: Colors.transparent,
        title: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Builder(
                builder: (context) => IconButton(
                  icon: const Icon(Icons.menu, color: AppTheme.darkGray),
                  onPressed: () {
                    Scaffold.of(context).openDrawer();
                  },
                ),
              ),
              const Spacer(),
              GestureDetector(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ProfileScreen(user: widget.user),
                    ),
                  );
                },
                child: CircleAvatar(
                  radius: 20,
                  backgroundColor: AppTheme.primaryGreen,
                  child: Text(
                    (widget.user.fullName?.isNotEmpty == true
                            ? widget.user.fullName![0]
                            : widget.user.username[0])
                        .toUpperCase(),
                    style: const TextStyle(color: AppTheme.white),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: const BoxDecoration(
                color: AppTheme.primaryGreen,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: AppTheme.white,
                    child: Text(
                      (widget.user.fullName?.isNotEmpty == true
                              ? widget.user.fullName![0]
                              : widget.user.username[0])
                          .toUpperCase(),
                      style: const TextStyle(
                        color: AppTheme.primaryGreen,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    widget.user.fullName ?? widget.user.username,
                    style: const TextStyle(
                      color: AppTheme.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (widget.user.employeeType != null)
                    Text(
                      widget.user.employeeType!.toUpperCase(),
                      style: const TextStyle(
                        color: AppTheme.white,
                        fontSize: 14,
                      ),
                    ),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.home),
              title: const Text('Home'),
              selected: _currentNavIndex == 0,
              onTap: () {
                Navigator.pop(context);
                _onNavTap(0);
              },
            ),
            ListTile(
              leading: const Icon(Icons.receipt_long),
              title: const Text('My Statement'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => DriverStatementScreen(user: widget.user),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.person),
              title: const Text('Profile'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => ProfileScreen(user: widget.user),
                  ),
                );
              },
            ),
          ],
        ),
      ),
      body: IndexedStack(
        index: _currentNavIndex,
        children: [
          _buildHomeTab(),
          _buildPickupTab(),
          _buildDeliveryTab(),
          _buildPerformanceTab(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentNavIndex,
        onTap: _onNavTap,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppTheme.primaryGreen,
        unselectedItemColor: AppTheme.darkGray,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.local_shipping),
            label: 'Pickup List',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.delivery_dining),
            label: 'Delivery List',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.trending_up),
            label: 'Performance',
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(
    BuildContext context,
    String title,
    String value,
    IconData icon, {
    Color? color,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color ?? AppTheme.primaryGreen, size: 32),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: color ?? AppTheme.primaryGreen,
                    fontWeight: FontWeight.bold,
                  ),
            ),
            Text(
              title,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(
    BuildContext context,
    String label,
    bool isSelected,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryGreen : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? AppTheme.primaryGreen : AppTheme.lightGray,
            width: 1,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: isSelected ? AppTheme.white : AppTheme.darkGray,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
          ),
        ),
      ),
    );
  }
}