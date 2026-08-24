import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/pos_transaction.dart';

String _generateTransactionId() {
  final now = DateTime.now();
  final random = Random().nextInt(999999).toString().padLeft(6, '0');
  return 'TX-${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}-$random';
}

/// Mock payment-request lifecycle. Real version: POST creates a pending
/// request the backend can associate with a BioID once the customer
/// authenticates on their own device (docs/roadmap.md Phase 5 — this needs
/// a new backend concept, since today's POST /payments assumes the
/// customer's own app is the caller, not a merchant terminal).
class PaymentRequestNotifier extends StateNotifier<PosTransaction?> {
  PaymentRequestNotifier() : super(null);

  void create(double amount) {
    state = PosTransaction(
      id: _generateTransactionId(),
      amount: amount,
      status: PosTransactionStatus.waitingForCustomer,
      createdAt: DateTime.now(),
    );
  }

  /// Stands in for the customer authenticating on their own device and the
  /// backend confirming via BioRouter — there's no second device in this
  /// mock, so the terminal itself triggers it (see WaitingScreen).
  Future<void> simulateCustomerAuthentication() async {
    final current = state;
    if (current == null) return;
    await Future<void>.delayed(const Duration(milliseconds: 800));
    state = current.copyWith(status: PosTransactionStatus.completed);
  }

  void cancel() {
    final current = state;
    if (current == null) return;
    state = current.copyWith(status: PosTransactionStatus.cancelled);
  }

  void reset() => state = null;
}

final paymentRequestProvider =
    StateNotifierProvider<PaymentRequestNotifier, PosTransaction?>((ref) => PaymentRequestNotifier());
