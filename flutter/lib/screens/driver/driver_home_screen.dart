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

class _DriverHomeScreenState extends State<DriverHomeScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  List<Order> _orders = [];
  bool _isLoading = true;
  int _currentNavIndex = 0;
  
  // Tab controller and task-related state
  late TabController _tabController;
  List<Order> _taskOrders = [];
  bool _isLoadingTasks = false;
  String? _selectedTaskStatus;
  bool _tasksLoaded = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(_handleTabChange);
    _loadOrders();
  }

  @override
  void dispose() {
    _tabController.removeListener(_handleTabChange);
    _tabController.dispose();
    super.dispose();
  }

  void _handleTabChange() {
    if (_tabController.index == 1 && !_tasksLoaded) {
      // Load tasks when Tasks tab is first selected with default 'All' filter
      _loadTaskOrders(status: null);
    }
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

  Future<void> _loadTaskOrders({String? status}) async {
    setState(() {
      _isLoadingTasks = true;
    });

    try {
      final response = await _apiService.getOrders(
        length: 50,
        status: status,
      );
      setState(() {
        _taskOrders = response.data;
        _isLoadingTasks = false;
        _selectedTaskStatus = status;
        _tasksLoaded = true;
      });
    } catch (e) {
      setState(() {
        _isLoadingTasks = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading tasks: ${e.toString()}')),
        );
      }
    }
  }

  void _onNavTap(int index) {
    setState(() {
      _currentNavIndex = index;
    });

    // Navigate to different screens based on index
    switch (index) {
      case 0:
        // Already on home, do nothing
        break;
      case 1:
        // Statement
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => DriverStatementScreen(user: widget.user),
          ),
        );
        break;
      case 2:
        // Performance
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => DriverPerformanceScreen(user: widget.user),
          ),
        );
        break;
      case 3:
        // Profile
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ProfileScreen(user: widget.user),
          ),
        );
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Filter to show only assigned orders (drivers see only their orders)
    final assignedOrders = _orders;

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
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFFF8F9FA),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 2,
                  offset: const Offset(0, 1),
                ),
              ],
            ),
            child: Column(
              children: [
                Container(
                  height: 1,
                  color: AppTheme.lightGray.withOpacity(0.5),
                ),
                TabBar(
                  controller: _tabController,
                  labelColor: AppTheme.primaryGreen,
                  unselectedLabelColor: AppTheme.darkGray,
                  indicatorColor: AppTheme.primaryGreen,
                  indicatorWeight: 3,
                  indicatorSize: TabBarIndicatorSize.label,
                  labelStyle: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                  ),
                  unselectedLabelStyle: const TextStyle(
                    fontWeight: FontWeight.normal,
                    fontSize: 16,
                  ),
                  tabs: const [
                    Tab(text: 'Home'),
                    Tab(text: 'Tasks'),
                  ],
                ),
              ],
            ),
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
                setState(() {
                  _currentNavIndex = 0;
                });
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
              leading: const Icon(Icons.trending_up),
              title: const Text('Performance'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => DriverPerformanceScreen(user: widget.user),
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
      body: TabBarView(
        controller: _tabController,
        children: [
          // Home Tab
          RefreshIndicator(
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
                            QuickActionButton(
                              icon: Icons.qr_code_scanner,
                              label: 'Scan',
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => ScanActionScreen(user: widget.user),
                                  ),
                                );
                              },
                            ),
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
                            QuickActionButton(
                              icon: Icons.local_offer,
                              label: 'Promo',
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const PromoScreen(),
                                  ),
                                );
                              },
                            ),
                            QuickActionButton(
                              icon: Icons.account_balance_wallet,
                              label: 'Top Up',
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => const TopUpScreen(),
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
          ),
          // Tasks Tab
          RefreshIndicator(
            onRefresh: () => _loadTaskOrders(status: _selectedTaskStatus),
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
                            _selectedTaskStatus == null,
                            () => _loadTaskOrders(status: null),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildFilterChip(
                            context,
                            'Assigned',
                            _selectedTaskStatus == 'assigned',
                            () => _loadTaskOrders(status: 'assigned'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildFilterChip(
                            context,
                            'In Transit',
                            _selectedTaskStatus == 'in_transit',
                            () => _loadTaskOrders(status: 'in_transit'),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Tasks List
                  if (_isLoadingTasks)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Center(child: CircularProgressIndicator()),
                    )
                  else if (_taskOrders.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(32),
                      child: Center(
                        child: Column(
                          children: [
                            Icon(
                              Icons.assignment_outlined,
                              size: 64,
                              color: AppTheme.lightGray,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'No tasks',
                              style: Theme.of(context).textTheme.bodyLarge,
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    ..._taskOrders.map((order) => OrderCard(
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
          ),
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
            icon: Icon(Icons.receipt_long),
            label: 'Statement',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.trending_up),
            label: 'Performance',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
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

