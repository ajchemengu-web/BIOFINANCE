import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/bio_id.dart';
import '../../repositories/bioid_repository.dart';
import '../authentication/auth_providers.dart';

/// Fetches (or issues, on first login) the current user's BioID.
/// Re-fetches whenever the session's authenticated status flips.
final bioIdProvider = FutureProvider<BioId>((ref) {
  ref.watch(authProvider.select((s) => s.isAuthenticated));
  return ref.watch(bioIdRepositoryProvider).fetchOrIssue();
});
