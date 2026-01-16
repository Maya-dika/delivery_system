import 'package:flutter/material.dart';
import '../../models/user.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import 'package:intl/intl.dart';

class DriverStatementScreen extends StatefulWidget {
  final User user;

  const DriverStatementScreen({
    super.key,
    required this.user,
  });

  @override
  State<DriverStatementScreen> createState() => _DriverStatementScreenState();
}

class _DriverStatementScreenState extends State<DriverStatementScreen> {
  final ApiService _apiService = ApiService();
  Map<String, dynamic>? _statementData;
  bool _isLoading = true;
  DateTime? _fromDate;
  DateTime? _toDate;

  @override
  void initState() {
    super.initState();
    _loadStatement();
  }

  Future<void> _loadStatement() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final from = _fromDate != null
          ? DateFormat('yyyy-MM-dd').format(_fromDate!)
          : null;
      final to =
          _toDate != null ? DateFormat('yyyy-MM-dd').format(_toDate!) : null;

      final data = await _apiService.getDriverStatement(from: from, to: to);
      setState(() {
        _statementData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading statement: ${e.toString()}')),
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
      _loadStatement();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Driver Statement'),
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
          : _statementData == null
              ? const Center(child: Text('No statement data available'))
              : RefreshIndicator(
                  onRefresh: _loadStatement,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Summary Card
                        if (_statementData!['totals'] != null)
                          Card(
                            color: AppTheme.primaryGreen.withOpacity(0.1),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Summary',
                                    style:
                                        Theme.of(context).textTheme.titleLarge,
                                  ),
                                  const SizedBox(height: 16),
                                  _buildSummaryRow(
                                    context,
                                    'Total Orders',
                                    _statementData!['totals']['nb_orders']
                                        .toString(),
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Total Fees',
                                    _statementData!['totals']['total_fees'] ??
                                        '\$0',
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Total Commission',
                                    _statementData!['totals']
                                            ['total_commission'] ??
                                        '\$0',
                                  ),
                                  _buildSummaryRow(
                                    context,
                                    'Profit',
                                    _statementData!['totals']['profit'] ?? '\$0',
                                    isProfit: true,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        const SizedBox(height: 16),
                        
                        // Date Range Info
                        if (_fromDate != null && _toDate != null)
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Date Range:',
                                    style:
                                        Theme.of(context).textTheme.titleMedium,
                                  ),
                                  Text(
                                    '${DateFormat('MMM dd, yyyy').format(_fromDate!)} - ${DateFormat('MMM dd, yyyy').format(_toDate!)}',
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        const SizedBox(height: 16),
                        
                        // Statement Data
                        Text(
                          'Daily Breakdown',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        if (_statementData!['data'] != null &&
                            (_statementData!['data'] as List).isNotEmpty)
                          ...(_statementData!['data'] as List).map((item) =>
                              _buildStatementItem(context, item))
                        else
                          const Card(
                            child: Padding(
                              padding: EdgeInsets.all(16),
                              child: Center(
                                child: Text('No data for selected period'),
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

  Widget _buildStatementItem(BuildContext context, Map<String, dynamic> item) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        title: Text(
          item['date'] ?? '',
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

