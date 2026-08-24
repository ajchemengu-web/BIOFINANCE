/// Mirrors backend/app/schemas/providers.py ProviderConnectionResponse.
/// `id` is the connection's UUID — routing policy references providers by
/// this id, not by provider_code (a user could reconnect the same provider).
class ProviderConnection {
  const ProviderConnection({required this.id, required this.providerCode, required this.status});

  final String id;
  final String providerCode;
  final String status;

  bool get connected => status == 'CONNECTED';

  factory ProviderConnection.fromJson(Map<String, dynamic> json) => ProviderConnection(
        id: json['id'] as String,
        providerCode: json['provider_code'] as String,
        status: json['status'] as String,
      );
}

const providerDisplayNames = {'MPESA': 'M-PESA', 'EQUITY': 'Equity', 'AIRTEL': 'Airtel Money'};

String providerDisplayName(String code) => providerDisplayNames[code] ?? code;
