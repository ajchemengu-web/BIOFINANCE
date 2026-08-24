import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Aggregated + per-provider balances for the BioWallet dashboard.
/// Uses mock data in Phase 1, wired to GET /balances in Phase 2.
final balanceProvider = StateProvider<Object?>((ref) => null);
