import 'employee.dart';

class User {
  final int? id;
  final String username;
  final String? token;
  final String? fullName;
  final String? email;
  final String? phoneNumber;
  final String? userType;
  final Employee? employee;
  final String? employeeType;
  final int? supplierId;

  User({
    this.id,
    required this.username,
    this.token,
    this.fullName,
    this.email,
    this.phoneNumber,
    this.userType,
    this.employee,
    this.employeeType,
    this.supplierId,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'] ?? '',
      token: json['token'],
      fullName: json['full_name'],
      email: json['email'],
      phoneNumber: json['phone_number'],
      userType: json['user_type'],
      employee: json['employee'] != null 
          ? Employee.fromJson(json['employee'] as Map<String, dynamic>)
          : null,
      employeeType: json['employee_type'] ?? json['employee']?['employee_type'],
      supplierId: json['supplier_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'token': token,
      'full_name': fullName,
      'email': email,
      'phone_number': phoneNumber,
      'user_type': userType,
      'employee': employee?.toJson(),
      'employee_type': employeeType,
      'supplier_id': supplierId,
    };
  }

  bool get isDriver => employee?.isDriver ?? false;
  bool get isManager => employee?.isManager ?? false;
  bool get isSupplier => userType == 'supplier';
}

