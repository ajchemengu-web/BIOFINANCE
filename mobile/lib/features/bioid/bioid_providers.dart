import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../authentication/auth_providers.dart';

/// Derives the current BioID display code from the mock session. Real
/// GET /bioid call lands in Phase 2.
final bioIdProvider = Provider<String?>((ref) => ref.watch(authProvider).bioIdCode);
