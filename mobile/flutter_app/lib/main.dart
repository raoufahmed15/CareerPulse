import 'package:flutter/material.dart';

void main() {
  runApp(const CareerPulseApp());
}

class CareerPulseApp extends StatelessWidget {
  const CareerPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CareerPulse',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CareerPulse')),
      body: const Center(
        child: Text(
          'Welcome to CareerPulse 🚀',
          style: TextStyle(fontSize: 20),
        ),
      ),
    );
  }
}
