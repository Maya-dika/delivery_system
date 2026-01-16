class Employee {
  final int? id;
  final String? name;
  final String? email;
  final String? phoneNumber;
  final String? employeeType;
  final bool? active;

  Employee({
    this.id,
    this.name,
    this.email,
    this.phoneNumber,
    this.employeeType,
    this.active,
  });

  factory Employee.fromJson(Map<String, dynamic>? json) {
    if (json == null) return Employee();
    return Employee(
      id: json['id'],
      name: json['name'],
      email: json['email'],
      phoneNumber: json['phone_number'],
      employeeType: json['employee_type'],
      active: json['active'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'phone_number': phoneNumber,
      'employee_type': employeeType,
      'active': active,
    };
  }

  bool get isDriver => employeeType == 'driver';
  bool get isManager => employeeType != null && 
    (employeeType == 'warehouse_manager' || 
     employeeType == 'admin' || 
     employeeType == 'internal_user');
}

