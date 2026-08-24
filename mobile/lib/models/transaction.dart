enum TransactionStatus { completed, declined, processing }

class AppTransaction {
  const AppTransaction({
    required this.id,
    required this.merchantName,
    required this.amount,
    required this.status,
    required this.provider,
    required this.createdAt,
    this.currency = 'KES',
  });

  final String id;
  final String merchantName;
  final double amount;
  final TransactionStatus status;
  final String provider;
  final DateTime createdAt;
  final String currency;
}
