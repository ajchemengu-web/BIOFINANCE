import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../authentication/auth_providers.dart';
import '../bioid/bioid_providers.dart';

/// Device/biometric management is still a stub pending Phase 2 hardware
/// binding — logout and BioID display are real.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final bioIdAsync = ref.watch(bioIdProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ListTile(title: const Text('Signed in as'), subtitle: Text(auth.email ?? '—')),
          ListTile(
            title: const Text('BioID'),
            subtitle: Text(bioIdAsync.when(
              data: (bioId) => bioId.code,
              loading: () => 'Loading…',
              error: (_, _) => '—',
            )),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Log out'),
            onTap: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
    );
  }
}
