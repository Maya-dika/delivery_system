import 'package:flutter/material.dart';
import '../../models/user.dart';
import '../../services/auth_service.dart';
import '../../utils/theme.dart';
import '../login/login_screen.dart';

class ProfileScreen extends StatelessWidget {
  final User user;

  const ProfileScreen({
    super.key,
    required this.user,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Profile Header
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 50,
                      backgroundColor: AppTheme.primaryGreen,
                      child: Text(
                        (user.fullName?.isNotEmpty == true
                                ? user.fullName![0]
                                : user.username[0])
                            .toUpperCase(),
                        style: const TextStyle(
                          fontSize: 40,
                          color: AppTheme.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      user.fullName ?? user.username,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    if (user.employeeType != null) ...[
                      const SizedBox(height: 8),
                      Chip(
                        label: Text(
                          user.employeeType!.toUpperCase(),
                          style: const TextStyle(
                            color: AppTheme.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        backgroundColor: AppTheme.primaryGreen,
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // User Information
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'User Information',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    _buildInfoRow(context, 'Username', user.username),
                    if (user.fullName != null)
                      _buildInfoRow(context, 'Full Name', user.fullName!),
                    if (user.email != null)
                      _buildInfoRow(context, 'Email', user.email!),
                    if (user.phoneNumber != null)
                      _buildInfoRow(context, 'Phone', user.phoneNumber!),
                    if (user.userType != null)
                      _buildInfoRow(context, 'User Type', user.userType!),
                  ],
                ),
              ),
            ),
            
            if (user.employee != null) ...[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Employee Information',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      if (user.employee!.name != null)
                        _buildInfoRow(context, 'Name', user.employee!.name!),
                      if (user.employee!.email != null)
                        _buildInfoRow(context, 'Email', user.employee!.email!),
                      if (user.employee!.phoneNumber != null)
                        _buildInfoRow(
                          context,
                          'Phone',
                          user.employee!.phoneNumber!,
                        ),
                      if (user.employee!.employeeType != null)
                        _buildInfoRow(
                          context,
                          'Employee Type',
                          user.employee!.employeeType!,
                        ),
                    ],
                  ),
                ),
              ),
            ],
            
            const SizedBox(height: 24),
            
            // Logout Button
            ElevatedButton.icon(
              onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Logout'),
                    content: const Text('Are you sure you want to logout?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Logout'),
                      ),
                    ],
                  ),
                );
                
                if (confirm == true) {
                  final authService = AuthService();
                  await authService.logout();
                  if (context.mounted) {
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (_) => const LoginScreen()),
                      (route) => false,
                    );
                  }
                }
              },
              icon: const Icon(Icons.logout),
              label: const Text('Logout'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: AppTheme.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: AppTheme.lightGray,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: AppTheme.darkGray),
            ),
          ),
        ],
      ),
    );
  }
}

