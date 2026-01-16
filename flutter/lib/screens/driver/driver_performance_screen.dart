import 'package:flutter/material.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import 'package:intl/intl.dart';

class DriverPerformanceScreen extends StatefulWidget {
  final User user;

  const DriverPerformanceScreen({
    super.key,
    required this.user,
  });

  @override
  State<DriverPerformanceScreen> createState() =>
      _DriverPerformanceScreenState();
}

class _DriverPerformanceScreenState extends State<DriverPerformanceScreen> {
  final ApiService _apiService = ApiService();
  Map<String, dynamic>? _performanceData;
  bool _isLoading = true;
  DateTime? _fromDate;
  DateTime? _toDate;

  @override
  void initState() {
    super.initState();
    _loadPerformance();
  }

  Future<void> _loadPerformance() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final from = _fromDate != null
          ? DateFormat('yyyy-MM-dd').format(_fromDate!)
          : null;
      final to =
          _toDate != null ? DateFormat('yyyy-MM-dd').format(_toDate!) : null;

      final data = await _apiService.getDriverPerformance(from: from, to: to);
      setState(() {
        _performanceData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error loading performance: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _selectDateRange() async {
    final now = DateTime.now();
    final firstDayOfMonth = DateTime(now.year, now.month, 1);

    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: now,
      initialDateRange: _fromDate != null && _toDate != null
          ? DateTimeRange(start: _fromDate!, end: _toDate!)
          : DateTimeRange(start: firstDayOfMonth, end: now),
    );

    if (picked != null) {
      setState(() {
        _fromDate = picked.start;
        _toDate = picked.end;
      });
      _loadPerformance();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Driver Performance'),
        actions: [
          IconButton(
            icon: const Icon(Icons.date_range),
            onPressed: _selectDateRange,
            tooltip: 'Select Date Range',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _performanceData == null
              ? const Center(child: Text('No performance data available'))
              : RefreshIndicator(
                  onRefresh: _loadPerformance,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Summary Card
                        if (_performanceData!['totals'] != null)
                          Card(
                            color: AppTheme.primaryGreen.withOpacity(0.1),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Overall Performance',
                                    style:
                                        Theme.of(context).textTheme.titleLarge,
                                  ),
                                  const SizedBox(height: 16),
                                  _buildSummaryRow(
                                    context,
                                    'Total Orders',
                                    _performanceData!['totals']['nb_orders']
                                        .toString(),
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Total Fees',
                                    _performanceData!['totals']
                                            ['total_fees'] ??
                                        '\$0',
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Total Commission',
                                    _performanceData!['totals']
                                            ['total_commission'] ??
                                        '\$0',
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Total Profit',
                                    _performanceData!['totals']['profit'] ??
                                        '\$0',
                                    isProfit: true,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        const SizedBox(height: 16),
                        
                        // Performance Data
                        Text(
                          'Driver Performance',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        if (_performanceData!['data'] != null &&
                            (_performanceData!['data'] as List).isNotEmpty)
                          ...(_performanceData!['data'] as List).map((item) =>
                              _buildPerformanceItem(context, item))
                        else
                          const Card(
                            child: Padding(
                              padding: EdgeInsets.all(16),
                              child: Center(
                                child: Text('No performance data available'),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildSummaryRow(
    BuildContext context,
    String label,
    String value, {
    bool isProfit = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isProfit ? AppTheme.primaryGreen : AppTheme.darkGray,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildPerformanceItem(
      BuildContext context, Map<String, dynamic> item) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.primaryGreen.withOpacity(0.2),
          child: const Icon(Icons.person, color: AppTheme.primaryGreen),
        ),
        title: Text(
          item['employee'] ?? 'Unknown',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            Text('Orders: ${item['nb_orders'] ?? 0}'),
            Text('Fees: ${item['total_fees'] ?? '\$0'}'),
            Text('Commission: ${item['total_commission'] ?? '\$0'}'),
          ],
        ),
        trailing: Text(
          item['profit'] ?? '\$0',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: AppTheme.primaryGreen,
                fontWeight: FontWeight.bold,
              ),
        ),
      ),
    );
  }
}

