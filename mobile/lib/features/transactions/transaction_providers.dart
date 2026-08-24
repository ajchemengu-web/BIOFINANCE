import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/transaction.dart';

final _seedTransactions = [
  AppTransaction(
    id: 'TX-20260820-000004',
    merchantName: 'Java House',
    amount: 450,
    status: TransactionStatus.completed,
    provider: 'MPESA',
    createdAt: DateTime.now().subtract(const Duration(days: 3)),
  ),
  AppTransaction(
    id: 'TX-20260818-000003',
    merchantName: 'Naivas Supermarket',
    amount: 3200,
    status: TransactionStatus.completed,
    provider: 'MPESA',
    createdAt: DateTime.now().subtract(const Duration(days: 5)),
  ),
];

/// Mock transaction history for Phase 1. Wired to GET /transactions in
/// Phase 2; entries here get appended by the mock payment flow in
/// features/payments so the demo journey (PRD §42) is visible end-to-end.
class TransactionNotifier extends StateNotifier<List<AppTransaction>> {
  TransactionNotifier() : super(_seedTransactions);

  void add(AppTransaction transaction) => state = [transaction, ...state];
}

final transactionProvider =
    StateNotifierProvider<TransactionNotifier, List<AppTransaction>>((ref) => TransactionNotifier());
