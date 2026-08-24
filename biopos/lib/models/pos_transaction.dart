enum PosTransactionStatus { waitingForCustomer, completed, declined, cancelled }

/// A payment request created by the merchant terminal (PRD §32). Distinct
/// from the customer app's Transaction model — BioPOS creates the request
/// before anyone has authenticated; the backend doesn't have this concept
/// yet (POST /payments today assumes the *customer's* own app calls it
/// after they've already authenticated). See docs/roadmap.md Phase 5.
class PosTransaction {
  const PosTransaction({
    required this.id,
    required this.amount,
    required this.status,
    required this.createdAt,
    this.currency = 'KES',
  });

  final String id;
  final double amount;
  final PosTransactionStatus status;
  final DateTime createdAt;
  final String currency;

  PosTransaction copyWith({PosTransactionStatus? status}) => PosTransaction(
        id: id,
        amount: amount,
        status: status ?? this.status,
        createdAt: createdAt,
        currency: currency,
      );
}
