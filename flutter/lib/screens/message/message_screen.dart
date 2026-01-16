import 'package:flutter/material.dart';
import '../../utils/theme.dart';

class MessageScreen extends StatefulWidget {
  const MessageScreen({super.key});

  @override
  State<MessageScreen> createState() => _MessageScreenState();
}

class _MessageScreenState extends State<MessageScreen> {
  final List<MessageItem> _messages = [
    MessageItem(
      sender: 'Support Team',
      message: 'Your order has been confirmed',
      time: '10:30 AM',
      isUnread: true,
    ),
    MessageItem(
      sender: 'Delivery Team',
      message: 'Your package is out for delivery',
      time: 'Yesterday',
      isUnread: true,
    ),
    MessageItem(
      sender: 'Admin',
      message: 'Welcome to our delivery service',
      time: '2 days ago',
      isUnread: false,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Messages'),
      ),
      body: _messages.isEmpty
          ? Center(
              child: Text(
                'No messages',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            )
          : ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return Card(
                  margin: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AppTheme.primaryGreen,
                      child: Text(
                        message.sender[0].toUpperCase(),
                        style: const TextStyle(color: AppTheme.white),
                      ),
                    ),
                    title: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          message.sender,
                          style: TextStyle(
                            fontWeight: message.isUnread
                                ? FontWeight.bold
                                : FontWeight.normal,
                          ),
                        ),
                        if (message.isUnread)
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppTheme.primaryGreen,
                              shape: BoxShape.circle,
                            ),
                          ),
                      ],
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(message.message),
                        const SizedBox(height: 4),
                        Text(
                          message.time,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                    onTap: () {
                      setState(() {
                        message.isUnread = false;
                      });
                      // Navigate to chat detail
                    },
                  ),
                );
              },
            ),
    );
  }
}

class MessageItem {
  String sender;
  String message;
  String time;
  bool isUnread;

  MessageItem({
    required this.sender,
    required this.message,
    required this.time,
    required this.isUnread,
  });
}

