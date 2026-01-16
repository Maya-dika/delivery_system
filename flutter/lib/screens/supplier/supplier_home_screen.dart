import 'package:flutter/material.dart';
import '../../models/order_request.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../widgets/order_request_card.dart';
import '../../widgets/quick_action_button.dart';
import '../profile/profile_screen.dart';
import '../scan/scan_action_screen.dart';
import '../pickup/pickup_screen.dart';
import '../dropoff/dropoff_screen.dart';
import '../promo/promo_screen.dart';
import '../topup/topup_screen.dart';
import 'order_request_detail_modal.dart';
import 'create_request_screen.dart';

class SupplierHomeScreen extends StatefulWidget {
  final User user;

  const SupplierHomeScreen({
    super.key,
    required this.user,
  });

  @override
  State<SupplierHomeScreen> createState() => _SupplierHomeScreenState();
}

class _SupplierHomeScreenState extends State<SupplierHomeScreen> {
  final ApiService _apiService = ApiService();
  List<OrderRequest> _orderRequests = [];
  bool _isLoading = true;
  int _currentNavIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadOrderRequests();
  }

  Future<void> _loadOrderRequests() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _apiService.getOrderRequests(length: 50);
      setState(() {
        _orderRequests = response.data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading order requests: ${e.toString()}')),
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
    // Calculate statistics
    final totalRequests = _orderRequests.length;
    final pendingRequests = _orderRequests.where((req) => 
      req.status.toLowerCase() == 'requested'
    ).length;
    final confirmedRequests = _orderRequests.where((req) => 
      req.status.toLowerCase() == 'confirmed'
    ).length;
    final pickedUpRequests = _orderRequests.where((req) => 
      req.status.toLowerCase() == 'picked_up'
    ).length;

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Builder(
              builder: (context) => IconButton(
                icon: const Icon(Icons.menu),
                onPressed: () {
                  Scaffold.of(context).openDrawer();
                },
              ),
            ),
            const Spacer(),
            // Create Request Button
            IconButton(
              icon: const Icon(Icons.add),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => CreateRequestScreen(user: widget.user),
                  ),
                ).then((refreshed) {
                  if (refreshed == true) {
                    _loadOrderRequests();
                  }
                });
              },
              tooltip: 'Create Request',
            ),
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
                  if (widget.user.userType != null)
                    Text(
                      widget.user.userType!.toUpperCase(),
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
      body: RefreshIndicator(
        onRefresh: _loadOrderRequests,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Supplier Stats Cards
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Expanded(
                      child: _buildStatCard(
                        context,
                        'Total Requests',
                        totalRequests.toString(),
                        Icons.description,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildStatCard(
                        context,
                        'Pending',
                        pendingRequests.toString(),
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
                        'Confirmed',
                        confirmedRequests.toString(),
                        Icons.check_circle,
                        color: AppTheme.primaryGreen,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildStatCard(
                        context,
                        'Picked Up',
                        pickedUpRequests.toString(),
                        color: Colors.blue,
                        Icons.local_shipping,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              
              // Quick Actions Section
            //   Padding(
            //     padding: const EdgeInsets.symmetric(horizontal: 16),
            //     child: Column(
            //       crossAxisAlignment: CrossAxisAlignment.start,
            //       children: [
            //         Text(
            //           'Quick Actions',
            //           style: Theme.of(context).textTheme.titleLarge,
            //         ),
            //         const SizedBox(height: 16),
            //         Row(
            //           mainAxisAlignment: MainAxisAlignment.spaceAround,
            //           children: [
            //             QuickActionButton(
            //               icon: Icons.qr_code_scanner,
            //               label: 'Scan',
            //               onTap: () {
            //                 Navigator.push(
            //                   context,
            //                   MaterialPageRoute(
            //                     builder: (_) => ScanActionScreen(user: widget.user),
            //                   ),
            //                 );
            //               },
            //             ),
            //             QuickActionButton(
            //               icon: Icons.local_shipping,
            //               label: 'Pick Up',
            //               onTap: () {
            //                 Navigator.push(
            //                   context,
            //                   MaterialPageRoute(
            //                     builder: (_) => const PickUpScreen(),
            //                   ),
            //                 );
            //               },
            //             ),
            //             QuickActionButton(
            //               icon: Icons.delivery_dining,
            //               label: 'Drop Off',
            //               onTap: () {
            //                 Navigator.push(
            //                   context,
            //                   MaterialPageRoute(
            //                     builder: (_) => const DropOffScreen(),
            //                   ),
            //                 );
            //               },
            //             ),
            //             QuickActionButton(
            //               icon: Icons.local_offer,
            //               label: 'Promo',
            //               onTap: () {
            //                 Navigator.push(
            //                   context,
            //                   MaterialPageRoute(
            //                     builder: (_) => const PromoScreen(),
            //                   ),
            //                 );
            //               },
            //             ),
            //             QuickActionButton(
            //               icon: Icons.account_balance_wallet,
            //               label: 'Top Up',
            //               onTap: () {
            //                 Navigator.push(
            //                   context,
            //                   MaterialPageRoute(
            //                     builder: (_) => const TopUpScreen(),
            //                   ),
            //                 );
            //               },
            //             ),
            //           ],
            //         ),
            //       ],
            //     ),
            //   ),
              const SizedBox(height: 24),
              
              // Order Requests Section
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  'My Order Requests (${_orderRequests.length})',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              const SizedBox(height: 16),
              
              // Order Requests List
              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_orderRequests.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(32),
                  child: Center(
                    child: Column(
                      children: [
                        Icon(
                          Icons.description_outlined,
                          size: 64,
                          color: AppTheme.lightGray,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'No order requests',
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      ],
                    ),
                  ),
                )
              else
                ..._orderRequests.map((request) => OrderRequestCard(
                      orderRequest: request,
                      onTap: () {
                        OrderRequestDetailModal.show(context, request);
                      },
                    )),
              const SizedBox(height: 80),
            ],
          ),
        ),
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
}
