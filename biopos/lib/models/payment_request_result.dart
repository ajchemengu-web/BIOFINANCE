/// Mirrors backend/app/schemas/payments.py PaymentResponse — the shape
/// returned by both POST /payments/request and GET /payments/{id}.
class PaymentRequestResult {
  const PaymentRequestResult({
    required this.id,
    required this.status,
    required this.amount,
    required this.currency,
    this.selectedProvider,
  });

  final String id;
  final String status;
  final double amount;
  final String currency;
  final String? selectedProvider;

  /// Matches backend/app/services/payment_service.py's state machine — once
  /// here, GET /payments/{id} won't change again on its own.
  bool get isTerminal => const {
        'COMPLETED',
        'DECLINED',
        'PROVIDER_UNAVAILABLE',
        'CANCELLED',
        'FAILED',
        'AUTHENTICATION_FAILED',
      }.contains(status);

  bool get isSuccessful => status == 'COMPLETED';

  factory PaymentRequestResult.fromJson(Map<String, dynamic> json) => PaymentRequestResult(
        id: json['id'] as String,
        status: json['status'] as String,
        amount: double.parse(json['amount'].toString()),
        currency: json['currency'] as String,
        selectedProvider: json['selected_provider'] as String?,
      );
}
