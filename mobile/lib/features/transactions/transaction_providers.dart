import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/transaction.dart';
import '../../repositories/transactions_repository.dart';
import '../authentication/auth_providers.dart';

/// Transaction history (GET /transactions, Phase 2/3).
final transactionProvider = FutureProvider<List<AppTransaction>>((ref) {
  ref.watch(authProvider.select((s) => s.isAuthenticated));
  return ref.watch(transactionsRepositoryProvider).list();
});
