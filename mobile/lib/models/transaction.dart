class PaymentAttempt {
  const PaymentAttempt({required this.providerCode, required this.result, this.providerReference});

  final String providerCode;
  final String result;
  final String? providerReference;

  factory PaymentAttempt.fromJson(Map<String, dynamic> json) => PaymentAttempt(
        providerCode: json['provider_code'] as String,
        result: json['result'] as String,
        providerReference: json['provider_reference'] as String?,
      );
}

/// Mirrors backend/app/schemas/transactions.py TransactionResponse.
class AppTransaction {
  const AppTransaction({
    required this.id,
    required this.amount,
    required this.status,
    required this.createdAt,
    this.selectedProvider,
    this.completedAt,
    this.currency = 'KES',
    this.attempts = const [],
  });

  final String id;
  final double amount;
  final String status;
  final String? selectedProvider;
  final DateTime createdAt;
  final DateTime? completedAt;
  final String currency;
  final List<PaymentAttempt> attempts;

  factory AppTransaction.fromJson(Map<String, dynamic> json) => AppTransaction(
        id: json['id'] as String,
        amount: double.parse(json['amount'].toString()),
        currency: json['currency'] as String? ?? 'KES',
        status: json['status'] as String,
        selectedProvider: json['selected_provider'] as String?,
        createdAt: DateTime.parse(json['created_at'] as String),
        completedAt:
            json['completed_at'] == null ? null : DateTime.parse(json['completed_at'] as String),
        attempts: ((json['attempts'] as List?) ?? [])
            .map((e) => PaymentAttempt.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
