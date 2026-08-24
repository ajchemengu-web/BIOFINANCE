import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/provider_balance.dart';
import '../../repositories/balances_repository.dart';
import '../providers/provider_connections_providers.dart';

/// Aggregated BioWallet balances (GET /balances, Phase 2). Re-fetches
/// whenever the set of connected providers changes.
final balanceProvider = FutureProvider<BalancesResult>((ref) {
  ref.watch(providerConnectionsProvider);
  return ref.watch(balancesRepositoryProvider).fetch();
});
