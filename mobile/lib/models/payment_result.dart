/// Mirrors backend/app/schemas/payments.py PaymentResponse — the shape
/// returned by POST /payments, distinct from (and narrower than) the
/// TransactionResponse returned by GET /transactions.
class PaymentResult {
  const PaymentResult({
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

  factory PaymentResult.fromJson(Map<String, dynamic> json) => PaymentResult(
        id: json['id'] as String,
        status: json['status'] as String,
        amount: double.parse(json['amount'].toString()),
        currency: json['currency'] as String,
        selectedProvider: json['selected_provider'] as String?,
      );
}
