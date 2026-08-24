import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the current session state (logged in / out, tokens).
/// Business logic lands in Phase 1 (docs/roadmap.md) once auth screens exist.
final authProvider = StateProvider<Object?>((ref) => null);
